# sakramenty/views.py

# === IMPORTY ===
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

# Importy ról
from konta.mixins import RolaWymaganaMixin
from konta.models import Rola

from osoby.models import Osoba
from .models import (
    Chrzest,
    PierwszaKomunia,
    Bierzmowanie,
    Malzenstwo,
    NamaszczenieChorych,
    Zgon,
)
from .forms import (
    ChrzestForm,
    PierwszaKomuniaForm,
    BierzmowanieForm,
    MalzenstwoForm,
    NamaszczenieChorychForm,
    ZgonForm,
)


# =============================================================================
# === CHRZEST
# =============================================================================

class ChrzestListaView(LoginRequiredMixin, ListView):
    model = Chrzest
    template_name = "sakramenty/chrzest_lista.html"
    context_object_name = "chrzty"
    paginate_by = 50

    def get_queryset(self):
        qs = Chrzest.objects.select_related("ochrzczony").order_by("-rok", "akt_nr")

        # filtrowanie po roku i wyszukiwanie
        szukaj = (self.request.GET.get("q") or "").strip()
        rok = (self.request.GET.get("rok") or "").strip()

        if rok:
            qs = qs.filter(rok=rok)

        if szukaj:
            # szukaj po nazwisku, imieniu albo nr aktu
            qs = qs.filter(
                Q(ochrzczony__nazwisko__icontains=szukaj)
                | Q(ochrzczony__imie_pierwsze__icontains=szukaj)
                | Q(akt_nr__icontains=szukaj)
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtr_q"] = self.request.GET.get("q", "")
        ctx["filtr_rok"] = self.request.GET.get("rok", "")
        return ctx


class ChrzestSzczegolyView(LoginRequiredMixin, DetailView):
    model = Chrzest
    template_name = "sakramenty/chrzest_szczegoly.html"
    context_object_name = "chrzest"


class ChrzestNowyView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Chrzest
    form_class = ChrzestForm
    template_name = "sakramenty/chrzest_formularz.html"
    osoba = None  # ustawiane, gdy wchodzimy z profilu osoby

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
            # blokada duplikatu
            if Chrzest.objects.filter(ochrzczony=self.osoba).exists():
                messages.warning(request, "Ta osoba ma już wpis chrztu.")
                return redirect(self.osoba.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if not self.osoba:
            return initial

        o = self.osoba
        initial["ochrzczony"] = o

        if getattr(o, "data_urodzenia", None):
            initial["data_urodzenia"] = o.data_urodzenia

        def full(first, last):
            return " ".join(x for x in [first or "", last or ""] if x).strip()

        ojciec_txt = full(getattr(o, "imie_ojca", ""), getattr(o, "nazwisko_ojca", ""))
        if ojciec_txt:
            initial["ojciec"] = ojciec_txt

        matka_txt = full(getattr(o, "imie_matki", ""), getattr(o, "nazwisko_matki", ""))
        if matka_txt:
            initial["matka"] = matka_txt

        rodowe = getattr(o, "nazwisko_matki_rodowe", "") or getattr(
            o, "nazwisko_rodowe", ""
        )
        if rodowe:
            initial["nazwisko_matki_rodowe"] = rodowe
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.osoba:
            obj.ochrzczony = self.osoba
        obj.save()
        messages.success(self.request, "Dodano wpis chrztu.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx

    def get_success_url(self):
        if self.object and self.object.ochrzczony_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.ochrzczony_id])
        return reverse_lazy("chrzest_lista")


class ChrzestEdycjaView(RolaWymaganaMixin, UpdateView): # <-- Poprawka: UpdateView
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Chrzest
    form_class = ChrzestForm
    template_name = "sakramenty/chrzest_formularz.html"
    success_url = reverse_lazy("chrzest_lista")


class ChrzestUsunView(RolaWymaganaMixin, DeleteView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Chrzest
    template_name = "sakramenty/chrzest_usun.html"
    success_url = reverse_lazy("chrzest_lista")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Wpis chrztu został usunięty.")
        return super().delete(request, *args, **kwargs)


class ChrzestListaDrukView(ChrzestListaView):
    template_name = "sakramenty/druki/chrzest_lista_druk.html"
    paginate_by = None


class ChrzestDrukView(LoginRequiredMixin, DetailView):
    model = Chrzest
    template_name = "sakramenty/druki/chrzest_druk.html"
    context_object_name = "chrzest"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        osoba = self.object.ochrzczony
        bierzm = (
            Bierzmowanie.objects.filter(osoba=osoba)
            .select_related("parafia")
            .order_by("-data_bierzmowania", "-rok")
            .first()
        )
        ctx["bierzmowanie"] = bierzm
        ctx["today"] = timezone.localdate()
        ctx["http_request"] = self.request
        return ctx


# =============================================================================
# === I KOMUNIA ŚW.
# =============================================================================

class KomuniaListaView(LoginRequiredMixin, ListView): # <-- Poprawka: ListView i LoginRequiredMixin
    model = PierwszaKomunia
    template_name = "sakramenty/komunia_lista.html"
    context_object_name = "komunie"
    paginate_by = 20
    ordering = ["-rok", "osoba__nazwisko", "osoba__imie_pierwsze"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("osoba")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            for slowo in q.split():
                qs = qs.filter(
                    Q(osoba__nazwisko__icontains=slowo)
                    | Q(osoba__imie_pierwsze__icontains=slowo)
                    | Q(parafia__nazwa__icontains=slowo) # Poprawka: Model Komunii ma pole parafia (nie tekst)
                    | Q(rok__icontains=slowo)
                )
        return qs


class KomuniaSzczegolyView(LoginRequiredMixin, DetailView):
    model = PierwszaKomunia
    template_name = "sakramenty/komunia_szczegoly.html"
    context_object_name = "komunia"


class KomuniaNowaView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = PierwszaKomunia
    form_class = PierwszaKomuniaForm
    template_name = "sakramenty/komunia_formularz.html"
    osoba = None

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
            if PierwszaKomunia.objects.filter(osoba=self.osoba).exists():
                messages.warning(request, "Ta osoba ma już wpis I Komunii Św.")
                return redirect(self.osoba.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.osoba:
            initial["osoba"] = self.osoba
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.osoba:
            obj.osoba = self.osoba

        if PierwszaKomunia.objects.filter(osoba=obj.osoba).exists():
            form.add_error("osoba", "Dla tej osoby wpis I Komunii już istnieje.")
            return self.form_invalid(form)

        obj.save()
        messages.success(self.request, "Dodano wpis I Komunii Św.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx

    def get_success_url(self):
        if self.object and self.object.osoba_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.osoba_id])
        return reverse_lazy("komunia_lista")


class KomuniaEdycjaView(RolaWymaganaMixin, UpdateView): # <-- Poprawka: UpdateView
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = PierwszaKomunia
    form_class = PierwszaKomuniaForm
    template_name = "sakramenty/komunia_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany I Komunii.")
        return self.object.osoba.get_absolute_url()


class KomuniaUsunView(RolaWymaganaMixin, DeleteView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = PierwszaKomunia
    template_name = "sakramenty/komunia_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis I Komunii został usunięty.")
        return self.object.osoba.get_absolute_url()


class KomuniaListaDrukView(KomuniaListaView):
    template_name = "sakramenty/druki/komunia_lista_druk.html"
    paginate_by = None


class KomuniaDrukView(LoginRequiredMixin, DetailView):
    model = PierwszaKomunia
    template_name = "sakramenty/druki/komunia_druk.html"
    context_object_name = "komunia"


# =============================================================================
# === BIERZMOWANIE
# =============================================================================

class BierzmowanieListaView(LoginRequiredMixin, ListView): # <-- Poprawka: ListView i LoginRequiredMixin
    model = Bierzmowanie
    template_name = "sakramenty/bierzmowanie_lista.html"
    context_object_name = "bierzmowania"
    paginate_by = 20
    ordering = ["-rok", "osoba__nazwisko", "osoba__imie_pierwsze"]

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("osoba", "parafia", "szafarz")
        )
        q = (self.request.GET.get("q") or "").strip()
        if q:
            for slowo in q.split():
                qs = qs.filter(
                    Q(osoba__nazwisko__icontains=slowo)
                    | Q(osoba__imie_pierwsze__icontains=slowo)
                    | Q(akt_nr__icontains=slowo)
                    | Q(parafia__nazwa__icontains=slowo)
                    | Q(szafarz__imie_nazwisko__icontains=slowo) # Zakładam, że model Duchowny ma pole imie_nazwisko
                    | Q(rok__icontains=slowo)
                )
        return qs


class BierzmowanieSzczegolyView(LoginRequiredMixin, DetailView):
    model = Bierzmowanie
    template_name = "sakramenty/bierzmowanie_szczegoly.html"
    context_object_name = "bierzmowanie"


class BierzmowanieNoweView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Bierzmowanie
    form_class = BierzmowanieForm
    template_name = "sakramenty/bierzmowanie_formularz.html"
    osoba = None

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
            if Bierzmowanie.objects.filter(osoba=self.osoba).exists():
                messages.warning(request, "Ta osoba ma już wpis bierzmowania.")
                return redirect(self.osoba.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.osoba:
            initial["osoba"] = self.osoba
            # 1. AUTOMATYCZNE POBIERANIE:
            # Jeśli w profilu osoby jest już wpisane imię z bierzmowania,
            # wstaw je do formularza jako wartość początkową.
            if self.osoba.imie_bierzmowanie:
                initial["imie_bierzmowania"] = self.osoba.imie_bierzmowanie
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)
        
        # Jeśli dodajemy z profilu konkretnej osoby
        if self.osoba:
            obj.osoba = self.osoba

        # Sprawdzenie duplikatów
        if Bierzmowanie.objects.filter(osoba=obj.osoba).exists():
            form.add_error("osoba", "Dla tej osoby wpis bierzmowania już istnieje.")
            return self.form_invalid(form)

        obj.save()

        # 2. AKTUALIZACJA OSOBY:
        # Pobieramy imię wpisane w formularzu bierzmowania
        nowe_imie = form.cleaned_data.get("imie_bierzmowania")
        
        # Jeśli imię zostało podane, aktualizujemy profil osoby
        if nowe_imie:
            osoba_do_edycji = obj.osoba
            # Zapisujemy tylko jeśli jest inne (lub było puste), żeby nie robić zbędnych zapytań
            if osoba_do_edycji.imie_bierzmowanie != nowe_imie:
                osoba_do_edycji.imie_bierzmowanie = nowe_imie
                osoba_do_edycji.save()

        messages.success(self.request, "Dodano wpis bierzmowania i zaktualizowano dane osoby.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx

    def get_success_url(self):
        if self.object and self.object.osoba_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.osoba_id])
        return reverse_lazy("bierzmowanie_lista")


class BierzmowanieEdycjaView(RolaWymaganaMixin, UpdateView): # <-- Poprawka: UpdateView
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Bierzmowanie
    form_class = BierzmowanieForm
    template_name = "sakramenty/bierzmowanie_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany bierzmowania.")
        return self.object.osoba.get_absolute_url()


class BierzmowanieUsunView(RolaWymaganaMixin, DeleteView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Bierzmowanie
    template_name = "sakramenty/bierzmowanie_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis bierzmowania został usunięty.")
        return self.object.osoba.get_absolute_url()


class BierzmowanieListaDrukView(BierzmowanieListaView):
    template_name = "sakramenty/druki/bierzmowanie_lista_druk.html"
    paginate_by = None


class BierzmowanieDrukView(LoginRequiredMixin, DetailView):
    model = Bierzmowanie
    template_name = "sakramenty/druki/bierzmowanie_druk.html"
    context_object_name = "bierzmowanie"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        osoba = self.object.osoba
        chrzest = Chrzest.objects.filter(ochrzczony=osoba).first()
        ctx["chrzest"] = chrzest
        ctx["today"] = timezone.localdate()
        ctx["http_request"] = self.request
        return ctx


# =============================================================================
# === MAŁŻEŃSTWO
# =============================================================================

class MalzenstwoListaView(LoginRequiredMixin, ListView): # <-- Poprawka: ListView i LoginRequiredMixin
    model = Malzenstwo
    template_name = "sakramenty/malzenstwo_lista.html"
    context_object_name = "malzenstwa"
    paginate_by = 20
    ordering = ["-rok", "malzonek_a__nazwisko", "malzonek_b__nazwisko"]

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("malzonek_a", "malzonek_b", "parafia", "swiadek_urzedowy")
        )
        q = (self.request.GET.get("q") or "").strip()
        if q:
            for slowo in q.split():
                qs = qs.filter(
                    Q(malzonek_a__nazwisko__icontains=slowo)
                    | Q(malzonek_a__imie_pierwsze__icontains=slowo)
                    | Q(malzonek_b__nazwisko__icontains=slowo)
                    | Q(malzonek_b__imie_pierwsze__icontains=slowo)
                    | Q(rok__icontains=slowo)
                    | Q(akt_nr__icontains=slowo)
                    | Q(parafia__nazwa__icontains=slowo)
                    | Q(swiadek_urzedowy__imie_nazwisko__icontains=slowo) # Zakładam pole imie_nazwisko
                )
        return qs


class MalzenstwoSzczegolyView(LoginRequiredMixin, DetailView):
    model = Malzenstwo
    template_name = "sakramenty/malzenstwo_szczegoly.html"
    context_object_name = "malzenstwo"


class MalzenstwoNoweView(RolaWymaganaMixin, CreateView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Malzenstwo
    form_class = MalzenstwoForm
    template_name = "sakramenty/malzenstwo_formularz.html"
    malzonek_a = None

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.malzonek_a = get_object_or_404(Osoba, pk=osoba_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.malzonek_a:
            initial["malzonek_a"] = self.malzonek_a.pk
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["malzonek_a_obj"] = self.malzonek_a
        return kwargs

    def form_valid(self, form):
        if self.malzonek_a:
            form.instance.malzonek_a = self.malzonek_a
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["malzonek_a"] = self.malzonek_a
        return ctx

    def get_success_url(self):
        if self.object.malzonek_a_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.malzonek_a_id])
        return reverse_lazy("malzenstwo_lista")


class MalzenstwoEdycjaView(RolaWymaganaMixin, UpdateView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Malzenstwo
    form_class = MalzenstwoForm
    template_name = "sakramenty/malzenstwo_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany małżeństwa.")
        return self.object.malzonek_a.get_absolute_url()


class MalzenstwoUsunView(RolaWymaganaMixin, DeleteView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Malzenstwo
    template_name = "sakramenty/malzenstwo_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis małżeństwa został usunięty.")
        return self.object.malzonek_a.get_absolute_url()


class MalzenstwoListaDrukView(MalzenstwoListaView):
    template_name = "sakramenty/druki/malzenstwo_lista_druk.html"
    paginate_by = None


class MalzenstwoDrukView(LoginRequiredMixin, DetailView):
    model = Malzenstwo
    template_name = "sakramenty/druki/malzenstwo_druk.html"
    context_object_name = "malzenstwo"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        malzenstwo = self.object
        chrzest_a = Chrzest.objects.filter(ochrzczony=malzenstwo.malzonek_a).first()
        chrzest_b = Chrzest.objects.filter(ochrzczony=malzenstwo.malzonek_b).first()
        ctx["chrzest_a"] = chrzest_a
        ctx["chrzest_b"] = chrzest_b
        ctx["today"] = timezone.localdate()
        ctx["http_request"] = self.request
        return ctx


# =============================================================================
# === NAMASZCZENIE CHORYCH
# =============================================================================

class NamaszczenieListaView(LoginRequiredMixin, ListView):
    model = NamaszczenieChorych
    template_name = "sakramenty/namaszczenie_lista.html"
    context_object_name = "namaszczenia"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            NamaszczenieChorych.objects.all()
            .select_related("osoba", "szafarz")
            .order_by("-data", "osoba__nazwisko", "osoba__imie_pierwsze") # Poprawka: Dodane sortowanie
        )
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(osoba__nazwisko__icontains=q)
                | Q(osoba__imie_pierwsze__icontains=q)
                | Q(miejsce__icontains=q)
                | Q(szafarz__imie_nazwisko__icontains=q) # Zakładam pole imie_nazwisko
            )
        return qs


class NamaszczenieSzczegolyView(LoginRequiredMixin, DetailView):
    model = NamaszczenieChorych
    template_name = "sakramenty/namaszczenie_szczegoly.html"
    context_object_name = "namaszczenie"


class NamaszczenieNoweView(RolaWymaganaMixin, CreateView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = NamaszczenieChorych
    form_class = NamaszczenieChorychForm
    template_name = "sakramenty/namaszczenie_formularz.html"
    osoba = None

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.osoba:
            initial["osoba"] = self.osoba
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx

    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.osoba is not None:
            obj.osoba = self.osoba
        else:
            osoba_z_form = form.cleaned_data.get("osoba")
            if not osoba_z_form:
                form.add_error("osoba", "Wybierz osobę.")
                return self.form_invalid(form)
            obj.osoba = osoba_z_form
        obj.save()
        messages.success(self.request, "Dodano wpis posługi/namaszczenia.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        if self.object and self.object.osoba_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.osoba.pk])
        return reverse_lazy("namaszczenie_lista")


class NamaszczenieEdycjaView(RolaWymaganaMixin, UpdateView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = NamaszczenieChorych
    form_class = NamaszczenieChorychForm
    template_name = "sakramenty/namaszczenie_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany posługi/namaszczenia.")
        return self.object.osoba.get_absolute_url()


class NamaszczenieUsunView(RolaWymaganaMixin, DeleteView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = NamaszczenieChorych
    template_name = "sakramenty/namaszczenie_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis posługi/namaszczenia został usunięty.")
        return self.object.osoba.get_absolute_url()


class NamaszczenieListaDrukView(NamaszczenieListaView):
    template_name = "sakramenty/druki/namaszczenie_lista_druk.html"
    paginate_by = None


class NamaszczenieDrukView(LoginRequiredMixin, DetailView):
    model = NamaszczenieChorych
    template_name = "sakramenty/druki/namaszczenie_druk.html"
    context_object_name = "namaszczenie"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["today"] = timezone.localdate()
        return ctx


# =============================================================================
# === ZGON
# =============================================================================

class ZgonListaView(LoginRequiredMixin, ListView):
    model = Zgon
    template_name = "sakramenty/zgon_lista.html"
    context_object_name = "zgony"
    paginate_by = 20
    ordering = ["-rok", "osoba__nazwisko", "osoba__imie_pierwsze"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("osoba")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            for slowo in q.split():
                qs = qs.filter(
                    Q(osoba__nazwisko__icontains=slowo)
                    | Q(osoba__imie_pierwsze__icontains=slowo)
                    | Q(akt_nr__icontains=slowo)
                    | Q(cmentarz__icontains=slowo)
                    | Q(rok__icontains=slowo)
                )
        return qs


class ZgonSzczegolyView(LoginRequiredMixin, DetailView):
    model = Zgon
    template_name = "sakramenty/zgon_szczegoly.html"
    context_object_name = "zgon"


class ZgonNowyView(RolaWymaganaMixin, CreateView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Zgon
    form_class = ZgonForm
    template_name = "sakramenty/zgon_formularz.html"
    osoba = None

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
            if Zgon.objects.filter(osoba=self.osoba).exists():
                messages.warning(request, "Ta osoba ma już wpis zgonu.")
                return redirect(self.osoba.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.osoba:
            initial["osoba"] = self.osoba
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx

    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.osoba:
            obj.osoba = self.osoba

        if Zgon.objects.filter(osoba=obj.osoba).exists():
            form.add_error("osoba", "Dla tej osoby wpis zgonu już istnieje.")
            return self.form_invalid(form)

        obj.save()
        messages.success(self.request, "Dodano wpis o zgonie.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        if self.object and self.object.osoba_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.osoba_id])
        return reverse_lazy("zgon_lista")


class ZgonEdycjaView(RolaWymaganaMixin, UpdateView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Zgon
    form_class = ZgonForm
    template_name = "sakramenty/zgon_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany przy zgonie.")
        return self.object.osoba.get_absolute_url()


class ZgonUsunView(RolaWymaganaMixin, DeleteView): # <-- Poprawka: RolaWymaganaMixin
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Zgon
    template_name = "sakramenty/zgon_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis zgonu został usunięty.")
        return self.object.osoba.get_absolute_url()


class ZgonListaDrukView(ZgonListaView):
    template_name = "sakramenty/druki/zgon_lista_druk.html"
    paginate_by = None


class ZgonDrukView(LoginRequiredMixin, DetailView):
    model = Zgon
    template_name = "sakramenty/druki/zgon_druk.html"
    context_object_name = "zgon"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        zgon = self.object
        chrzest = Chrzest.objects.filter(ochrzczony=zgon.osoba).first()
        ctx["chrzest"] = chrzest
        ctx["today"] = timezone.localdate()
        ctx["http_request"] = self.request
        return ctx