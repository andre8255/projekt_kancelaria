# sakramenty/views.py

# === IMPORTY ===
from django.views.generic import View
from parafia.utils_pdf import render_to_pdf
from django.conf import settings
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

from konta.utils import zapisz_log

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

        # 1. Filtrowanie po frazie (nazwisko, imię, nr aktu)
        szukaj = (self.request.GET.get("q") or "").strip()
        if szukaj:
            qs = qs.filter(
                Q(ochrzczony__nazwisko__icontains=szukaj)
                | Q(ochrzczony__imie_pierwsze__icontains=szukaj)
                | Q(akt_nr__icontains=szukaj)
            )

        # 2. Filtrowanie po ROKU
        rok = (self.request.GET.get("rok") or "").strip()
        if rok:
            qs = qs.filter(rok=rok)

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
    osoba = None

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
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
        self.object = obj  # WAŻNE – żeby get_success_url miało self.object

        zapisz_log(
            self.request,
            "DODANIE_CHRZTU",
            self.object,
            opis=f"Dodano chrzest: akt {self.object.akt_nr}"
        )

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


class ChrzestEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Chrzest
    form_class = ChrzestForm
    template_name = "sakramenty/chrzest_formularz.html"
    success_url = reverse_lazy("chrzest_lista")

    def form_valid(self, form):
        response = super().form_valid(form)
        zapisz_log(
            self.request,
            "EDYCJA_CHRZTU",
            self.object,
            opis=f"Zmieniono wpis chrztu: akt {self.object.akt_nr}"
        )
        messages.success(self.request, "Zapisano zmiany przy chrzcie.")
        return response


class ChrzestUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Chrzest
    template_name = "sakramenty/chrzest_usun.html"
    success_url = reverse_lazy("chrzest_lista")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        opis = f"Usunięto wpis chrztu: akt {self.object.akt_nr}"
        zapisz_log(
            request,
            "USUNIECIE_CHRZTU",
            self.object,
            opis=opis
        )
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

class ChrzestPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        chrzest = get_object_or_404(Chrzest, pk=kwargs['pk'])
        cel_wydania = request.GET.get('cel', '')
        bierzmowanie = Bierzmowanie.objects.filter(osoba=chrzest.ochrzczony).first()
        
        context = {
            'chrzest': chrzest,
            'bierzmowanie': bierzmowanie,
            'today': timezone.localdate(),
            'cel_wydania': cel_wydania,
            # 'parafia': ... -> zostanie dodana automatycznie przez render_to_pdf
        }
        
        filename = f"Swiadectwo_Chrztu_{chrzest.ochrzczony.nazwisko}.pdf"
        return render_to_pdf('sakramenty/druki/chrzest_pdf.html', context, filename)

class ChrzestListaPDFView(ChrzestListaView):
    """
    Generuje PDF z listy chrztów, zachowując aktywne filtry (np. rok, wyszukiwanie).
    """
    def render_to_response(self, context, **response_kwargs):
        context['today'] = timezone.now()
        filename = f"Wykaz_Chrztow_{timezone.localdate()}.pdf"
        return render_to_pdf('sakramenty/druki/chrzest_lista_pdf.html', context, filename)  

# =============================================================================
# === I KOMUNIA ŚW.
# =============================================================================

class KomuniaListaView(LoginRequiredMixin, ListView):
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
                    | Q(parafia__nazwa__icontains=slowo)
                )
        
        rok = (self.request.GET.get("rok") or "").strip()
        if rok and rok.isdigit():
            qs = qs.filter(rok=rok)

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
        self.object = obj

        zapisz_log(
            self.request,
            "DODANIE_KOMUNII",
            self.object,
            opis=f"Dodano wpis I Komunii: {self.object.osoba}"
        )

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


class KomuniaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = PierwszaKomunia
    form_class = PierwszaKomuniaForm
    template_name = "sakramenty/komunia_formularz.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        zapisz_log(
            self.request,
            "EDYCJA_KOMUNII",
            self.object,
            opis=f"Zmieniono wpis I Komunii: {self.object.osoba}"
        )
        messages.success(self.request, "Zapisano zmiany I Komunii.")
        return response

    def get_success_url(self):
        return self.object.osoba.get_absolute_url()


class KomuniaUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = PierwszaKomunia
    template_name = "sakramenty/komunia_usun.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        opis = f"Usunięto wpis I Komunii: {self.object.osoba}"
        zapisz_log(
            request,
            "USUNIECIE_KOMUNII",
            self.object,
            opis=opis
        )
        messages.success(request, "Wpis I Komunii został usunięty.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.osoba.get_absolute_url()



class KomuniaListaDrukView(KomuniaListaView):
    template_name = "sakramenty/druki/komunia_lista_druk.html"
    paginate_by = None


class KomuniaDrukView(LoginRequiredMixin, DetailView):
    model = PierwszaKomunia
    template_name = "sakramenty/druki/komunia_druk.html"
    context_object_name = "komunia"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["today"] = timezone.localdate() 
        return ctx

class KomuniaListaPDFView(KomuniaListaView):
    """
    Generuje PDF z listy I Komunii, zachowując aktywne filtry.
    """
    def render_to_response(self, context, **response_kwargs):
        context['today'] = timezone.now()
        filename = f"Wykaz_Komunii_{timezone.localdate()}.pdf"
        return render_to_pdf('sakramenty/druki/komunia_lista_pdf.html', context, filename)


# =============================================================================
# === BIERZMOWANIE
# =============================================================================

class BierzmowanieListaView(LoginRequiredMixin, ListView):
    model = Bierzmowanie
    template_name = "sakramenty/bierzmowanie_lista.html"
    context_object_name = "bierzmowania"
    paginate_by = 20
    ordering = ["-rok", "osoba__nazwisko", "osoba__imie_pierwsze"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("osoba", "parafia", "szafarz")
        
        q = (self.request.GET.get("q") or "").strip()
        if q:
            for slowo in q.split():
                qs = qs.filter(
                    Q(osoba__nazwisko__icontains=slowo)
                    | Q(osoba__imie_pierwsze__icontains=slowo)
                    | Q(akt_nr__icontains=slowo)
                    | Q(parafia__nazwa__icontains=slowo)
                )
        
        rok = (self.request.GET.get("rok") or "").strip()
        if rok and rok.isdigit():
            qs = qs.filter(rok=rok)
            
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
            if self.osoba.imie_bierzmowanie:
                initial["imie_bierzmowania"] = self.osoba.imie_bierzmowanie
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.osoba:
            obj.osoba = self.osoba

        if Bierzmowanie.objects.filter(osoba=obj.osoba).exists():
            form.add_error("osoba", "Dla tej osoby wpis bierzmowania już istnieje.")
            return self.form_invalid(form)

        obj.save()
        self.object = obj

        nowe_imie = form.cleaned_data.get("imie_bierzmowania")
        if nowe_imie:
            osoba_do_edycji = obj.osoba
            if osoba_do_edycji.imie_bierzmowanie != nowe_imie:
                osoba_do_edycji.imie_bierzmowanie = nowe_imie
                osoba_do_edycji.save()

        zapisz_log(
            self.request,
            "DODANIE_BIERZMOWANIA",
            self.object,
            opis=f"Dodano wpis bierzmowania: {self.object.osoba}"
        )

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


class BierzmowanieEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Bierzmowanie
    form_class = BierzmowanieForm
    template_name = "sakramenty/bierzmowanie_formularz.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        zapisz_log(
            self.request,
            "EDYCJA_BIERZMOWANIA",
            self.object,
            opis=f"Zmieniono wpis bierzmowania: {self.object.osoba}"
        )
        messages.success(self.request, "Zapisano zmiany bierzmowania.")
        return response

    def get_success_url(self):
        return self.object.osoba.get_absolute_url()


class BierzmowanieUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Bierzmowanie
    template_name = "sakramenty/bierzmowanie_usun.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        opis = f"Usunięto wpis bierzmowania: {self.object.osoba}"
        zapisz_log(
            request,
            "USUNIECIE_BIERZMOWANIA",
            self.object,
            opis=opis
        )
        messages.success(request, "Wpis bierzmowania został usunięty.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
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

class BierzmowanieListaPDFView(BierzmowanieListaView):
    """
    Generuje PDF z listy bierzmowań, zachowując aktywne filtry.
    """
    def render_to_response(self, context, **response_kwargs):
        context['today'] = timezone.now()
        filename = f"Wykaz_Bierzmowan_{timezone.localdate()}.pdf"
        return render_to_pdf('sakramenty/druki/bierzmowanie_lista_pdf.html', context, filename)

# =============================================================================
# === MAŁŻEŃSTWO
# =============================================================================

class MalzenstwoListaView(LoginRequiredMixin, ListView):
    model = Malzenstwo
    template_name = "sakramenty/malzenstwo_lista.html"
    context_object_name = "malzenstwa"
    paginate_by = 20
    ordering = ["-rok", "malzonek_a__nazwisko", "malzonek_b__nazwisko"]

    def get_queryset(self):
        qs = super().get_queryset().select_related("malzonek_a", "malzonek_b", "parafia")
        
        q = (self.request.GET.get("q") or "").strip()
        if q:
            for slowo in q.split():
                qs = qs.filter(
                    Q(malzonek_a__nazwisko__icontains=slowo)
                    | Q(malzonek_a__nazwisko_rodowe__icontains=slowo)
                    | Q(malzonek_a__imie_pierwsze__icontains=slowo)
                    | Q(malzonek_b__nazwisko__icontains=slowo)
                    | Q(malzonek_b__nazwisko_rodowe__icontains=slowo)
                    | Q(malzonek_b__imie_pierwsze__icontains=slowo)
                    | Q(akt_nr__icontains=slowo)
                    | Q(parafia__nazwa__icontains=slowo)
                    | Q(akt_nr__icontains=slowo)  
                    | Q(parafia__nazwa__icontains=slowo)
                    | Q(parafia_opis_reczny__icontains=slowo)
                    | Q(swiadek_urzedowy__imie_nazwisko__icontains=slowo)
                    | Q(swiadek_urzedowy_opis_reczny__icontains=slowo)  
                )

        rok = (self.request.GET.get("rok") or "").strip()
        if rok and rok.isdigit():
            qs = qs.filter(rok=rok)

        return qs


class MalzenstwoSzczegolyView(LoginRequiredMixin, DetailView):
    model = Malzenstwo
    template_name = "sakramenty/malzenstwo_szczegoly.html"
    context_object_name = "malzenstwo"


class MalzenstwoNoweView(RolaWymaganaMixin, CreateView):
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
        response = super().form_valid(form)

        zapisz_log(
            self.request,
            "DODANIE_MALZENSTWA",
            self.object,
            opis=f"Dodano małżeństwo: {self.object.malzonek_a} + {self.object.malzonek_b}"
        )

        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["malzonek_a"] = self.malzonek_a
        return ctx

    def get_success_url(self):
        if self.object.malzonek_a_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.malzonek_a_id])
        return reverse_lazy("malzenstwo_lista")


class MalzenstwoEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Malzenstwo
    form_class = MalzenstwoForm
    template_name = "sakramenty/malzenstwo_formularz.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        zapisz_log(
            self.request,
            "EDYCJA_MALZENSTWA",
            self.object,
            opis=f"Zmieniono dane małżeństwa: {self.object.malzonek_a} + {self.object.malzonek_b}"
        )
        messages.success(self.request, "Zapisano zmiany małżeństwa.")
        return response

    def get_success_url(self):
        return self.object.malzonek_a.get_absolute_url()


class MalzenstwoUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Malzenstwo
    template_name = "sakramenty/malzenstwo_usun.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        opis = f"Usunięto małżeństwo: {self.object.malzonek_a} + {self.object.malzonek_b}"
        zapisz_log(
            request,
            "USUNIECIE_MALZENSTWA",
            self.object,
            opis=opis
        )
        messages.success(request, "Wpis małżeństwa został usunięty.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
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

class MalzenstwoListaPDFView(MalzenstwoListaView):
    """
    Generuje PDF z listy małżeństw, zachowując aktywne filtry.
    """
    def render_to_response(self, context, **response_kwargs):
        context['today'] = timezone.now()
        filename = f"Wykaz_Malzenstw_{timezone.localdate()}.pdf"
        return render_to_pdf('sakramenty/druki/malzenstwo_lista_pdf.html', context, filename)

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
            .order_by("-data", "osoba__nazwisko")
        )
        
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(osoba__nazwisko__icontains=q)
                | Q(osoba__imie_pierwsze__icontains=q)
                | Q(miejsce__icontains=q)
            )

        rok = (self.request.GET.get("rok") or "").strip()
        if rok and rok.isdigit():
            qs = qs.filter(data__year=rok)

        return qs


class NamaszczenieSzczegolyView(LoginRequiredMixin, DetailView):
    model = NamaszczenieChorych
    template_name = "sakramenty/namaszczenie_szczegoly.html"
    context_object_name = "namaszczenie"


class NamaszczenieNoweView(RolaWymaganaMixin, CreateView):
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
        self.object = obj

        zapisz_log(
            self.request,
            "DODANIE_NAMASZCZENIA",
            self.object,
            opis=f"Dodano wpis namaszczenia/posługi: {self.object.osoba}"
        )

        messages.success(self.request, "Dodano wpis posługi/namaszczenia.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        if self.object and self.object.osoba_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.osoba.pk])
        return reverse_lazy("namaszczenie_lista")


class NamaszczenieEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = NamaszczenieChorych
    form_class = NamaszczenieChorychForm
    template_name = "sakramenty/namaszczenie_formularz.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        zapisz_log(
            self.request,
            "EDYCJA_NAMASZCZENIA",
            self.object,
            opis=f"Zmieniono wpis namaszczenia/posługi: {self.object.osoba}"
        )
        messages.success(self.request, "Zapisano zmiany posługi/namaszczenia.")
        return response

    def get_success_url(self):
        return self.object.osoba.get_absolute_url()


class NamaszczenieUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = NamaszczenieChorych
    template_name = "sakramenty/namaszczenie_usun.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        opis = f"Usunięto wpis namaszczenia/posługi: {self.object.osoba}"
        zapisz_log(
            request,
            "USUNIECIE_NAMASZCZENIA",
            self.object,
            opis=opis
        )
        messages.success(request, "Wpis posługi/namaszczenia został usunięty.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
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

class NamaszczenieListaPDFView(NamaszczenieListaView):
    """
    Generuje PDF z listy namaszczeń, zachowując aktywne filtry.
    """
    def render_to_response(self, context, **response_kwargs):
        context['today'] = timezone.now()
        filename = f"Wykaz_Namaszczen_{timezone.localdate()}.pdf"
        return render_to_pdf('sakramenty/druki/namaszczenie_lista_pdf.html', context, filename)


# =============================================================================
# === ZGON
# =============================================================================

class ZgonListaView(LoginRequiredMixin, ListView):
    model = Zgon
    template_name = "sakramenty/zgon_lista.html"
    context_object_name = "zgony"
    paginate_by = 20
    ordering = ["-rok", "osoba__nazwisko"]

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
                )

        rok = (self.request.GET.get("rok") or "").strip()
        if rok and rok.isdigit():
            qs = qs.filter(rok=rok)
        return qs

class ZgonSzczegolyView(LoginRequiredMixin, DetailView):
    model = Zgon
    template_name = "sakramenty/zgon_szczegoly.html"
    context_object_name = "zgon"


class ZgonNowyView(RolaWymaganaMixin, CreateView):
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
        self.object = obj

        zapisz_log(
            self.request,
            "DODANIE_ZGONU",
            self.object,
            opis=f"Dodano wpis zgonu: {self.object.osoba}"
        )

        messages.success(self.request, "Dodano wpis o zgonie.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        if self.object and self.object.osoba_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.osoba_id])
        return reverse_lazy("zgon_lista")


class ZgonEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Zgon
    form_class = ZgonForm
    template_name = "sakramenty/zgon_formularz.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        zapisz_log(
            self.request,
            "EDYCJA_ZGONU",
            self.object,
            opis=f"Zmieniono wpis zgonu: {self.object.osoba}"
        )
        messages.success(self.request, "Zapisano zmiany przy zgonie.")
        return response

    def get_success_url(self):
        return self.object.osoba.get_absolute_url()


class ZgonUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Zgon
    template_name = "sakramenty/zgon_usun.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        opis = f"Usunięto wpis zgonu: {self.object.osoba}"
        zapisz_log(
            request,
            "USUNIECIE_ZGONU",
            self.object,
            opis=opis
        )
        messages.success(request, "Wpis zgonu został usunięty.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
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

class ZgonListaPDFView(ZgonListaView):
    """
    Generuje PDF z listy zgonów, zachowując aktywne filtry.
    """
    def render_to_response(self, context, **response_kwargs):
        context['today'] = timezone.now()
        filename = f"Wykaz_Zgonow_{timezone.localdate()}.pdf"
        return render_to_pdf('sakramenty/druki/zgon_lista_pdf.html', context, filename)



# --- I KOMUNIA PDF ---
class KomuniaPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        komunia = get_object_or_404(PierwszaKomunia, pk=kwargs['pk'])
        # Pobieramy chrzest, aby mieć dane rodziców/urodzenia w razie braków
        chrzest = Chrzest.objects.filter(ochrzczony=komunia.osoba).first()
        
        context = {
            'komunia': komunia,
            'chrzest': chrzest,
            'today': timezone.localdate(),
            # 'parafia' - zostanie dodana automatycznie
        }
        filename = f"Komunia_{komunia.osoba.nazwisko}.pdf"
        return render_to_pdf('sakramenty/druki/komunia_pdf.html', context, filename)

# --- BIERZMOWANIE PDF ---
class BierzmowaniePDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        bierzmowanie = get_object_or_404(Bierzmowanie, pk=kwargs['pk'])
        
        # Pobieramy chrzest tej osoby, aby wypełnić sekcję o chrzcie
        chrzest = Chrzest.objects.filter(ochrzczony=bierzmowanie.osoba).first()
        
        context = {
            'bierzmowanie': bierzmowanie,
            'chrzest': chrzest,
            'today': timezone.localdate(),
        }
        filename = f"Bierzmowanie_{bierzmowanie.osoba.nazwisko}.pdf"
        return render_to_pdf('sakramenty/druki/bierzmowanie_pdf.html', context, filename)

# --- MAŁŻEŃSTWO PDF ---
class MalzenstwoPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        malzenstwo = get_object_or_404(Malzenstwo, pk=kwargs['pk'])
        
        # Pobieramy chrzty małżonków, aby mieć dane o rodzicach i urodzeniu
        chrzest_a = Chrzest.objects.filter(ochrzczony=malzenstwo.malzonek_a).first()
        chrzest_b = Chrzest.objects.filter(ochrzczony=malzenstwo.malzonek_b).first()
        
        context = {
            'malzenstwo': malzenstwo,
            'chrzest_a': chrzest_a,
            'chrzest_b': chrzest_b,
            'today': timezone.localdate(),
            # 'parafia': ... -> zostanie dodana automatycznie przez render_to_pdf
        }
        
        filename = f"Slub_{malzenstwo.malzonek_a.nazwisko}_{malzenstwo.malzonek_b.nazwisko}.pdf"
        return render_to_pdf('sakramenty/druki/malzenstwo_pdf.html', context, filename)

#--- NAMASZCZENIE PDF ---

class NamaszczeniePDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        namaszczenie = get_object_or_404(NamaszczenieChorych, pk=kwargs['pk'])
        
        context = {
            'namaszczenie': namaszczenie,
            'today': timezone.localdate(),
            # 'parafia' - zostanie dodana automatycznie
        }
        filename = f"Namaszczenie_{namaszczenie.osoba.nazwisko}.pdf"
        return render_to_pdf('sakramenty/druki/namaszczenie_pdf.html', context, filename)


# --- ZGON PDF --

class ZgonPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        zgon = get_object_or_404(Zgon, pk=kwargs['pk'])
        
        # Pobieramy chrzest (żeby mieć dokładne dane rodziców)
        chrzest = Chrzest.objects.filter(ochrzczony=zgon.osoba).first()
        
        # Pobieramy ostatnie namaszczenie (czasem wpisuje się na świadectwie zgonu)
        ostatnie_namaszczenie = NamaszczenieChorych.objects.filter(osoba=zgon.osoba).order_by('-data').first()
        
        context = {
            'zgon': zgon,
            'chrzest': chrzest,
            'namaszczenie': ostatnie_namaszczenie,
            'today': timezone.localdate(),
            # 'parafia' - dodane automatycznie
        }
        filename = f"Zgon_{zgon.osoba.nazwisko}.pdf"
        return render_to_pdf('sakramenty/druki/zgon_pdf.html', context, filename)