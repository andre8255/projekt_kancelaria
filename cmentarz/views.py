# cmentarz/views.py

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from konta.mixins import RolaWymaganaMixin
from konta.models import Rola
from konta.utils import zapisz_log          # <<< DODANY IMPORT
from parafia.utils_pdf import render_to_pdf

from .forms import GrobForm, PochowanyForm, SektorForm
from .models import Grob, Pochowany, Sektor


# =============================================================================
# GROBY
# =============================================================================

class GrobListaView(LoginRequiredMixin, ListView):
    model = Grob
    template_name = "cmentarz/lista.html"
    context_object_name = "groby"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Grob.objects
            .select_related("sektor", "dysponent")
            .prefetch_related("pochowani__osoba")
        )

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(rzad__icontains=q)
                | Q(numer__icontains=q)
                | Q(pochowani__osoba__nazwisko__icontains=q)
                | Q(pochowani__osoba__imie_pierwsze__icontains=q)
            ).distinct()

        sektor = self.request.GET.get("sektor")
        if sektor:
            qs = qs.filter(sektor_id=sektor)

        return qs.order_by("sektor", "numer")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sektory"] = Sektor.objects.all()
        return ctx


class GrobSzczegolyView(LoginRequiredMixin, DetailView):
    model = Grob
    template_name = "cmentarz/szczegoly.html"
    context_object_name = "grob"


class GrobNowyView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Grob
    form_class = GrobForm
    template_name = "cmentarz/formularz.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        # LOG
        zapisz_log(
            self.request,
            "DODANIE_GROBU",
            self.object,
            opis=f"Dodano grób: sektor {self.object.sektor} nr {self.object.numer}",
        )

        messages.success(self.request, "Dodano nowy grób.")
        return response

    def get_success_url(self):
        return reverse_lazy("cmentarz:grob_szczegoly", args=[self.object.pk])


class GrobEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Grob
    form_class = GrobForm
    template_name = "cmentarz/formularz.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        # LOG
        zapisz_log(
            self.request,
            "EDYCJA_GROBU",
            self.object,
            opis=f"Zmieniono dane grobu: sektor {self.object.sektor} nr {self.object.numer}",
        )

        messages.success(self.request, "Zapisano zmiany w karcie grobu.")
        return response

    def get_success_url(self):
        return reverse_lazy("cmentarz:grob_szczegoly", args=[self.object.pk])


class GrobUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Grob
    template_name = "cmentarz/grob_usun.html"
    success_url = reverse_lazy("cmentarz:grob_lista")

    def post(self, request, *args, **kwargs):
        # pobieramy obiekt PRZED usunięciem
        self.object = self.get_object()

        grob_id = self.object.pk
        sektor = self.object.sektor
        numer = self.object.numer

        # najpierw wykonujemy standardowe usunięcie
        response = super().post(request, *args, **kwargs)

        # a teraz zapisujemy log – obiekt już nie istnieje, więc:
        zapisz_log(
            request,
            "USUNIECIE_GROBU",
            None,  # obiektu już nie ma
            opis=f"Usunięto grób: sektor {sektor} / nr {numer}",
            model="Grob",
            obiekt_id=grob_id,
        )

        messages.success(request, "Grób został usunięty z ewidencji.")
        return response

# =============================================================================
# POCHOWANI
# =============================================================================

class PochowanyNowyView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Pochowany
    form_class = PochowanyForm
    template_name = "cmentarz/pochowany_formularz.html"

    def dispatch(self, request, *args, **kwargs):
        self.grob = get_object_or_404(Grob, pk=kwargs["grob_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        pochowany = form.save(commit=False)
        pochowany.grob = self.grob
        pochowany.save()

        # LOG
        osoba_txt = f"{pochowany.osoba.nazwisko} {pochowany.osoba.imie_pierwsze}"
        zapisz_log(
            self.request,
            "DODANIE_POCHOWANEGO",
            pochowany,
            opis=f"Dodano osobę {osoba_txt} do grobu sektor {self.grob.sektor} nr {self.grob.numer}",
        )

        messages.success(self.request, "Dodano osobę do grobu.")
        return redirect(self.grob.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["grob"] = self.grob
        return ctx


class PochowanyUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Pochowany
    template_name = "cmentarz/pochowany_usun.html"

    def post(self, request, *args, **kwargs):
        # pobieramy obiekt PRZED usunięciem
        self.object = self.get_object()
        grob = self.object.grob
        osoba = self.object.osoba

        # LOG
        zapisz_log(
            request,
            "USUNIECIE_POCHOWANEGO_Z_GROBU",
            self.object,
            opis=(
                f"Usunięto pochowanego {osoba} "
                f"z grobu sektor {grob.sektor} / nr {grob.numer}"
            ),
        )

        # usuwamy wpis pochówku
        self.object.delete()

        # POWIADOMIENIE
        messages.success(request, "Osoba została usunięta z grobu.")

        # powrót do karty grobu
        return redirect("cmentarz:grob_szczegoly", grob.pk)

# =============================================================================
# WYDRUKI (PDF)
# =============================================================================

class GrobPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        grob = get_object_or_404(Grob, pk=kwargs["pk"])
        context = {
            "grob": grob,
            "today": timezone.now(),
            # "parafia": ... (dodawane automatycznie)
        }
        filename = f"Karta_Grobu_{grob.sektor}_{grob.numer}.pdf"
        return render_to_pdf("cmentarz/druki/karta_grobu_pdf.html", context, filename)


# =============================================================================
# SEKTORY
# =============================================================================

class SektorListaView(LoginRequiredMixin, ListView):
    model = Sektor
    template_name = "cmentarz/sektor_lista.html"
    context_object_name = "sektory"


class SektorNowyView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Sektor
    form_class = SektorForm
    template_name = "cmentarz/sektor_formularz.html"
    success_url = reverse_lazy("cmentarz:sektor_lista")

    def form_valid(self, form):
        response = super().form_valid(form)

        zapisz_log(
            self.request,
            "DODANIE_SEKTORA",
            self.object,
            opis=f"Dodano sektor cmentarza: {self.object.nazwa}",
        )

        messages.success(self.request, "Dodano nowy sektor.")
        return response
