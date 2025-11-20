#rodziny/views.py
from django.utils import timezone
from django.conf import settings
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from parafia.utils_pdf import render_to_pdf
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
)

# Importy ról
from konta.mixins import RolaWymaganaMixin
from konta.models import Rola

from .models import Rodzina, CzlonkostwoRodziny,WizytaDuszpasterska
from .forms import RodzinaForm, DodajCzlonkaForm,WizytaForm
from sakramenty.models import (
    Chrzest,
    PierwszaKomunia,
    Bierzmowanie,
    Malzenstwo,
    NamaszczenieChorych,
    Zgon,
)


class RodzinaListaView(LoginRequiredMixin, ListView):
    model = Rodzina
    template_name = "rodziny/lista.html"
    context_object_name = "rodziny"
    paginate_by = 20

    def get_queryset(self):
        qs = Rodzina.objects.all().order_by(
            "miejscowosc", "ulica", "nr_domu", "nr_mieszkania", "nazwa"
        )
        q = (self.request.GET.get("q") or "").strip()
        if q:
            for slowo in q.split():
                qs = qs.filter(
                    Q(nazwa__icontains=slowo) |
                    Q(ulica__icontains=slowo) |
                    Q(miejscowosc__icontains=slowo)
                )
        return qs

class RodzinaSzczegolyView(LoginRequiredMixin, DetailView):
    model = Rodzina
    template_name = "rodziny/szczegoly.html"
    context_object_name = "rodzina"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rodzina = self.object

        # pobieramy członków rodziny (relacje CzlonkostwoRodziny)
        czlonkowie = (
            CzlonkostwoRodziny.objects
            .select_related("osoba")
            .filter(rodzina=rodzina)
        )

        # priorytet ról do sortowania
        PRIORYTET_ROLI = {
            "MAZ": 1,
            "ZONA": 2,
            "DZIECKO": 3,
            "INNA": 4,
        }

        def kolejnosc(cz):
            return PRIORYTET_ROLI.get(cz.rola, 99)

        posortowani = sorted(czlonkowie, key=kolejnosc)

        # teraz przygotowujemy bogatszą listę:
        # dla KAŻDEJ osoby w rodzinie sprawdzamy, czy ma wpisy w sakramentach
        wynik = []
        for wpis in posortowani:
            osoba = wpis.osoba

            ma_chrzest = Chrzest.objects.filter(ochrzczony=osoba).exists()
            ma_komunia = PierwszaKomunia.objects.filter(osoba=osoba).exists()
            ma_bierzmowanie = Bierzmowanie.objects.filter(osoba=osoba).exists()
            ma_malzenstwo = Malzenstwo.objects.filter(
                Q(malzonek_a=osoba) | Q(malzonek_b=osoba)
            ).exists()
            ma_namaszczenie = NamaszczenieChorych.objects.filter(osoba=osoba).exists()
            ma_zgon = Zgon.objects.filter(osoba=osoba).exists()

            wynik.append({
                "relacja": wpis,  # obiekt CzlonkostwoRodziny
                "osoba": osoba,
                "rola_display": wpis.get_rola_display(),
                "status_display": wpis.get_status_display() if wpis.status else "",
                "sakramenty": {
                    "chrzest": ma_chrzest,
                    "komunia": ma_komunia,
                    "bierzmowanie": ma_bierzmowanie,
                    "malzenstwo": ma_malzenstwo,
                    "namaszczenie": ma_namaszczenie,
                    "zgon": ma_zgon,
                }
            })

        ctx["czlonkowie_posortowani"] = wynik
        return ctx


class RodzinaNowaView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Rodzina
    form_class = RodzinaForm
    template_name = "rodziny/formularz.html"
    success_url = reverse_lazy("rodzina_lista")


class RodzinaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Rodzina
    form_class = RodzinaForm
    template_name = "rodziny/formularz.html"
    success_url = reverse_lazy("rodzina_lista")


class RodzinaUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Rodzina
    template_name = "rodziny/potwierdz_usuniecie.html"
    success_url = reverse_lazy("rodzina_lista")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                "Nie można usunąć tej rodziny, bo są do niej przypisane osoby."
            )
            return redirect(self.object.get_absolute_url())
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Rodzina została usunięta.")
        return super().delete(request, *args, **kwargs)

class RodzinaPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        rodzina = get_object_or_404(Rodzina, pk=kwargs['pk'])
        
        # --- LOGIKA POBIERANIA CZŁONKÓW I SAKRAMENTÓW ---
        # (Kopiujemy logikę, aby PDF miał te same dane co widok WWW)
        czlonkowie = CzlonkostwoRodziny.objects.select_related("osoba").filter(rodzina=rodzina)
        
        PRIORYTET_ROLI = {"MAZ": 1, "ZONA": 2, "DZIECKO": 3, "INNA": 4}
        posortowani = sorted(czlonkowie, key=lambda cz: PRIORYTET_ROLI.get(cz.rola, 99))
        
        wynik = []
        for wpis in posortowani:
            osoba = wpis.osoba
            ma_chrzest = Chrzest.objects.filter(ochrzczony=osoba).exists()
            ma_komunia = PierwszaKomunia.objects.filter(osoba=osoba).exists()
            ma_bierzmowanie = Bierzmowanie.objects.filter(osoba=osoba).exists()
            ma_malzenstwo = Malzenstwo.objects.filter(Q(malzonek_a=osoba) | Q(malzonek_b=osoba)).exists()
            
            wynik.append({
                "relacja": wpis,
                "osoba": osoba,
                "sakramenty": {
                    "chrzest": ma_chrzest,
                    "komunia": ma_komunia,
                    "bierzmowanie": ma_bierzmowanie,
                    "malzenstwo": ma_malzenstwo,
                }
            })
        
        context = {
            'rodzina': rodzina,
            'czlonkowie_posortowani': wynik,
            'today': timezone.localdate(),
            'parafia_nazwa': settings.PARAFIA_NAZWA,
            'parafia_miejscowosc': settings.PARAFIA_MIEJSCOWOSC,
        }
        
        filename = f"Kartoteka_{rodzina.nazwa}.pdf"
        return render_to_pdf('rodziny/druki/rodzina_pdf.html', context, filename)



# === WIZYTY DUSZPASTERSKIE ===

class WizytaNowaView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = WizytaDuszpasterska
    form_class = WizytaForm
    template_name = "rodziny/wizyta_formularz.html"

    def dispatch(self, request, *args, **kwargs):
        self.rodzina = get_object_or_404(Rodzina, pk=kwargs["rodzina_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        wizyta = form.save(commit=False)
        wizyta.rodzina = self.rodzina
        wizyta.save()
        messages.success(self.request, f"Dodano wizytę duszpasterską ({wizyta.rok}).")
        return redirect(self.rodzina.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rodzina"] = self.rodzina
        return ctx

class WizytaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = WizytaDuszpasterska
    form_class = WizytaForm
    template_name = "rodziny/wizyta_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zaktualizowano wizytę.")
        return self.object.rodzina.get_absolute_url()

class WizytaUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = WizytaDuszpasterska
    template_name = "rodziny/wizyta_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Usunięto wizytę.")
        return self.object.rodzina.get_absolute_url()



class RodzinaDrukView(LoginRequiredMixin, DetailView):
    model = Rodzina
    template_name = "rodziny/druki/rodzina_druk.html"
    context_object_name = "rodzina"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rodzina = self.object

        # --- Ta sama logika co w szczegółach, aby pobrać statusy sakramentów ---
        czlonkowie = (
            CzlonkostwoRodziny.objects
            .select_related("osoba")
            .filter(rodzina=rodzina)
        )

        PRIORYTET_ROLI = {
            "MAZ": 1, "ZONA": 2, "DZIECKO": 3, "INNA": 4,
        }
        def kolejnosc(cz): return PRIORYTET_ROLI.get(cz.rola, 99)
        posortowani = sorted(czlonkowie, key=kolejnosc)

        wynik = []
        for wpis in posortowani:
            osoba = wpis.osoba
            
            # Sprawdzamy sakramenty (True/False)
            ma_chrzest = Chrzest.objects.filter(ochrzczony=osoba).exists()
            ma_komunia = PierwszaKomunia.objects.filter(osoba=osoba).exists()
            ma_bierzmowanie = Bierzmowanie.objects.filter(osoba=osoba).exists()
            ma_malzenstwo = Malzenstwo.objects.filter(Q(malzonek_a=osoba) | Q(malzonek_b=osoba)).exists()
            # ma_zgon = Zgon.objects.filter(osoba=osoba).exists() # Opcjonalnie jeśli chcesz oznaczać zmarłych

            wynik.append({
                "relacja": wpis,
                "osoba": osoba,
                "sakramenty": {
                    "chrzest": ma_chrzest,
                    "komunia": ma_komunia,
                    "bierzmowanie": ma_bierzmowanie,
                    "malzenstwo": ma_malzenstwo,
                }
            })

        ctx["czlonkowie_posortowani"] = wynik
        ctx["today"] = timezone.localdate()
        return ctx



class DodajCzlonkaView(RolaWymaganaMixin, FormView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    template_name = "rodziny/dodaj_czlonka.html"
    form_class = DodajCzlonkaForm

    def dispatch(self, request, *args, **kwargs):
        self.rodzina = get_object_or_404(Rodzina, pk=kwargs["rodzina_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        czlonek = form.save(commit=False)
        czlonek.rodzina = self.rodzina
        czlonek.save()
        messages.success(self.request, "Osoba została przypisana do rodziny.")
        return redirect(self.rodzina.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rodzina"] = self.rodzina
        return ctx
    
class UsunCzlonkaZRodzinyView(RolaWymaganaMixin, View):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    template_name = "rodziny/usun_czlonka.html"

    def dispatch(self, request, *args, **kwargs):
        # pobierz rodzinę i członkostwo na początku, żeby mieć je w get/post
        self.rodzina = get_object_or_404(Rodzina, pk=kwargs["rodzina_pk"])
        self.czlonek = get_object_or_404(
            CzlonkostwoRodziny,
            pk=kwargs["czlonek_pk"],
            rodzina=self.rodzina,  # zabezpieczenie: członek MUSI należeć do tej rodziny
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, rodzina_pk, czlonek_pk):
        # pokazujemy stronę potwierdzenia
        return render(request, self.template_name, {
            "rodzina": self.rodzina,
            "czlonek": self.czlonek,
        })

    def post(self, request, rodzina_pk, czlonek_pk):
        # kasujemy tylko powiązanie, nie osobę
        osoba_txt = f"{self.czlonek.osoba.nazwisko} {self.czlonek.osoba.imie_pierwsze}"
        self.czlonek.delete()
        messages.success(
            request,
            f"Osoba {osoba_txt} została usunięta z tej rodziny."
        )
        return redirect(self.rodzina.get_absolute_url())

class CzlonkostwoUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = CzlonkostwoRodziny
    template_name = "rodziny/czlonek_usun.html"
    context_object_name = "czlonkostwo"

    def get_success_url(self):
        messages.success(self.request, "Osoba została usunięta z rodziny.")
        return self.object.rodzina.get_absolute_url()