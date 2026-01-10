# rodziny/views.py
from django.conf import settings  # (obecnie niewykorzystywane, ale zostawiam jeśli planujesz użyć)
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
)

from parafia.utils_pdf import render_to_pdf

# Importy ról / logowania akcji
from konta.mixins import RolaWymaganaMixin
from konta.models import Rola
from konta.utils import zapisz_log

from sakramenty.models import (
    Chrzest,
    PierwszaKomunia,
    Bierzmowanie,
    Malzenstwo,
    NamaszczenieChorych,
    Zgon,
)
from .forms import RodzinaForm, DodajCzlonkaForm, WizytaForm
from .models import Rodzina, CzlonkostwoRodziny, WizytaDuszpasterska


# =============================================================================
# LISTA / SZCZEGÓŁY RODZINY
# =============================================================================

class RodzinaListaView(LoginRequiredMixin, ListView):
    """
    Lista rodzin / kartotek z prostą wyszukiwarką (po nazwie i adresie).
    """
    model = Rodzina
    template_name = "rodziny/lista.html"
    context_object_name = "rodziny"
    paginate_by = 20

    def get_queryset(self):
        qs = Rodzina.objects.all()
        q = (self.request.GET.get("q") or "").strip()

        if q:
            for slowo in q.split():
                qs = qs.filter(
                    Q(nazwa__icontains=slowo) |
                    Q(ulica__icontains=slowo) |
                    Q(miejscowosc__icontains=slowo)
                )

        return qs.order_by(
            "nazwa",
            "miejscowosc",
            "ulica",
            "nr_domu",
            "nr_mieszkania",
        )


class RodzinaSzczegolyView(LoginRequiredMixin, DetailView):
    """
    Szczegóły konkretnej rodziny + członkowie + informacje o sakramentach.
    """
    model = Rodzina
    template_name = "rodziny/szczegoly.html"
    context_object_name = "rodzina"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rodzina = self.object

        # członkowie rodziny
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

        def kolejnosc(czlonkostwo: CzlonkostwoRodziny) -> int:
            return PRIORYTET_ROLI.get(czlonkostwo.rola, 99)

        posortowani = sorted(czlonkowie, key=kolejnosc)

        # budujemy listę zawierającą też info o sakramentach
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
                "relacja": wpis,
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
                },
            })

        ctx["czlonkowie_posortowani"] = wynik
        return ctx


# =============================================================================
# CRUD RODZINY
# =============================================================================

class RodzinaNowaView(RolaWymaganaMixin, CreateView):
    """
    Dodanie nowej rodziny / kartoteki.
    """
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Rodzina
    form_class = RodzinaForm
    template_name = "rodziny/formularz.html"
    success_url = reverse_lazy("rodzina_lista")

    def form_valid(self, form):
        response = super().form_valid(form)

        zapisz_log(
            self.request,
            "DODANIE_RODZINY",
            self.object,
            opis=f"Dodano rodzinę: {self.object.nazwa}",
        )

        messages.success(self.request, "Dodano nową rodzinę.")
        return response


class RodzinaEdycjaView(RolaWymaganaMixin, UpdateView):
    """
    Edycja istniejącej rodziny.
    """
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Rodzina
    form_class = RodzinaForm
    template_name = "rodziny/formularz.html"
    success_url = reverse_lazy("rodzina_lista")

    def form_valid(self, form):
        response = super().form_valid(form)

        zapisz_log(
            self.request,
            "EDYCJA_RODZINY",
            self.object,
            opis=f"Zmieniono dane rodziny: {self.object.nazwa}",
        )

        messages.success(self.request, "Zapisano zmiany danych rodziny.")
        return response


from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView

from konta.mixins import RolaWymaganaMixin
from konta.models import Rola
from konta.utils import zapisz_log
from .models import Rodzina


class RodzinaUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Rodzina
    template_name = "rodziny/potwierdz_usuniecie.html"
    success_url = reverse_lazy("rodzina_lista")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # snapshot danych (bo po delete obiekt znika)
        rodzina_id = self.object.pk
        rodzina_nazwa = getattr(self.object, "nazwa", str(self.object))

        try:
            response = super().post(request, *args, **kwargs)  # to wywoła delete()
        except ProtectedError:
            messages.error(request, "Nie można usunąć tej rodziny, bo są do niej przypisane osoby.")
            return redirect(self.object.get_absolute_url())

        zapisz_log(
    request,
    "USUNIECIE_RODZINY",
    None,
    opis=f"Usunięto rodzinę: {rodzina_nazwa}",
    model="Rodzina",
    obiekt_id=rodzina_id,
)
        messages.success(request, "Rodzina została usunięta.")
        return response

# =============================================================================
# DRUK / PDF RODZINY
# =============================================================================

class RodzinaPDFView(LoginRequiredMixin, View):
    """
    Generuje PDF kartoteki rodziny (członkowie + wizyty duszpasterskie).
    """

    def get(self, request, *args, **kwargs):
        rodzina = get_object_or_404(Rodzina, pk=kwargs["pk"])

        # --- 1. Członkowie rodziny ---
        czlonkowie = (
            CzlonkostwoRodziny.objects
            .select_related("osoba")
            .filter(rodzina=rodzina)
        )

        PRIORYTET_ROLI = {"MAZ": 1, "ZONA": 2, "DZIECKO": 3, "INNA": 4}
        posortowani = sorted(
            czlonkowie,
            key=lambda cz: PRIORYTET_ROLI.get(cz.rola, 99),
        )

        wynik_czlonkowie = []
        for wpis in posortowani:
            osoba = wpis.osoba
            wynik_czlonkowie.append({
                "relacja": wpis,
                "osoba": osoba,
                "sakramenty": {
                    "chrzest": Chrzest.objects.filter(ochrzczony=osoba).exists(),
                    "komunia": PierwszaKomunia.objects.filter(osoba=osoba).exists(),
                    "bierzmowanie": Bierzmowanie.objects.filter(osoba=osoba).exists(),
                    "malzenstwo": Malzenstwo.objects.filter(
                        Q(malzonek_a=osoba) | Q(malzonek_b=osoba)
                    ).exists(),
                    "namaszczenie": NamaszczenieChorych.objects.filter(osoba=osoba).exists(),
                    "zgon": Zgon.objects.filter(osoba=osoba).exists(),
                },
            })

        # --- 2. Wizyty duszpasterskie (najnowsze na górze) ---
        wizyty = (
            rodzina.wizyty
            .all()
            .select_related("ksiadz")
            .order_by("-rok", "-data_wizyty")
        )

        context = {
            "rodzina": rodzina,
            "czlonkowie_posortowani": wynik_czlonkowie,
            "wizyty": wizyty,
            "today": timezone.localdate(),
            # 'parafia' – dokładane automatycznie w render_to_pdf
        }

        # Bezpieczna nazwa pliku
        safe_name = "".join(c if c.isalnum() else "_" for c in rodzina.nazwa)
        filename = f"Kartoteka_{safe_name}.pdf"

        return render_to_pdf("rodziny/druki/rodzina_pdf.html", context, filename)


class RodzinaDrukView(LoginRequiredMixin, DetailView):
    """
    Widok „pod drukarkę” (HTML) – kartoteka rodziny.
    """
    model = Rodzina
    template_name = "rodziny/druki/rodzina_druk.html"
    context_object_name = "rodzina"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rodzina = self.object

        czlonkowie = (
            CzlonkostwoRodziny.objects
            .select_related("osoba")
            .filter(rodzina=rodzina)
        )

        PRIORYTET_ROLI = {"MAZ": 1, "ZONA": 2, "DZIECKO": 3, "INNA": 4}

        def kolejnosc(cz):
            return PRIORYTET_ROLI.get(cz.rola, 99)

        posortowani = sorted(czlonkowie, key=kolejnosc)

        wynik = []
        for wpis in posortowani:
            osoba = wpis.osoba

            ma_chrzest = Chrzest.objects.filter(ochrzczony=osoba).exists()
            ma_komunia = PierwszaKomunia.objects.filter(osoba=osoba).exists()
            ma_bierzmowanie = Bierzmowanie.objects.filter(osoba=osoba).exists()
            ma_malzenstwo = Malzenstwo.objects.filter(
                Q(malzonek_a=osoba) | Q(malzonek_b=osoba)
            ).exists()

            wynik.append({
                "relacja": wpis,
                "osoba": osoba,
                "sakramenty": {
                    "chrzest": ma_chrzest,
                    "komunia": ma_komunia,
                    "bierzmowanie": ma_bierzmowanie,
                    "malzenstwo": ma_malzenstwo,
                },
            })

        ctx["czlonkowie_posortowani"] = wynik
        ctx["today"] = timezone.localdate()
        return ctx


# =============================================================================
# WIZYTY DUSZPASTERSKIE
# =============================================================================

class WizytaNowaView(RolaWymaganaMixin, CreateView):
    """
    Dodanie wizyty duszpasterskiej dla konkretnej rodziny.
    """
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
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

        zapisz_log(
            self.request,
            "DODANIE_WIZYTY",
            wizyta,
            opis=f"Dodano wizytę duszpasterską ({wizyta.rok}) dla rodziny {self.rodzina.nazwa}",
        )

        messages.success(self.request, f"Dodano wizytę duszpasterską ({wizyta.rok}).")
        return redirect(self.rodzina.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rodzina"] = self.rodzina
        return ctx


class WizytaEdycjaView(RolaWymaganaMixin, UpdateView):
    """
    Edycja wizyty duszpasterskiej.
    """
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = WizytaDuszpasterska
    form_class = WizytaForm
    template_name = "rodziny/wizyta_formularz.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        zapisz_log(
            self.request,
            "EDYCJA_WIZYTY",
            self.object,
            opis=f"Zmieniono wizytę duszpasterską ({self.object.rok}) dla rodziny {self.object.rodzina.nazwa}",
        )

        return response

    def get_success_url(self):
        messages.success(self.request, "Zaktualizowano wizytę.")
        return self.object.rodzina.get_absolute_url()


class WizytaUsunView(RolaWymaganaMixin, DeleteView):
    """
    Usunięcie wizyty duszpasterskiej.
    """
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = WizytaDuszpasterska
    template_name = "rodziny/wizyta_usun.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        zapisz_log(
            request,
            "USUNIECIE_WIZYTY",
            self.object,
            opis=f"Usunięto wizytę duszpasterską ({self.object.rok}) "
                 f"dla rodziny {self.object.rodzina.nazwa}",
        )

        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Usunięto wizytę.")
        return self.object.rodzina.get_absolute_url()


# =============================================================================
# CZŁONKOWIE RODZINY
# =============================================================================

class DodajCzlonkaView(RolaWymaganaMixin, FormView):
    """
    Dodanie osoby (CzlonkostwoRodziny) do konkretnej rodziny.
    """
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    template_name = "rodziny/dodaj_czlonka.html"
    form_class = DodajCzlonkaForm

    def dispatch(self, request, *args, **kwargs):
        self.rodzina = get_object_or_404(Rodzina, pk=kwargs["rodzina_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["rodzina"] = self.rodzina
        return kwargs

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
    """
    Prosty widok potwierdzenia usunięcia członka z konkretnej rodziny.
    """
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    template_name = "rodziny/usun_czlonka.html"

    def dispatch(self, request, *args, **kwargs):
        # pobieramy rodzinę i członkostwo na starcie (używane w GET i POST)
        self.rodzina = get_object_or_404(Rodzina, pk=kwargs["rodzina_pk"])
        self.czlonek = get_object_or_404(
            CzlonkostwoRodziny,
            pk=kwargs["czlonek_pk"],
            rodzina=self.rodzina,  # zabezpieczenie: członek MUSI należeć do tej rodziny
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, rodzina_pk, czlonek_pk):
        # wyświetlenie strony z potwierdzeniem
        return render(
            request,
            self.template_name,
            {
                "rodzina": self.rodzina,
                "czlonek": self.czlonek,
            },
        )

    def post(self, request, rodzina_pk, czlonek_pk):
        osoba_txt = f"{self.czlonek.osoba.nazwisko} {self.czlonek.osoba.imie_pierwsze}"

        zapisz_log(
            request,
            "USUNIECIE_CZLONKA_RODZINY",
            self.czlonek,
            opis=f"Usunięto osobę {osoba_txt} z rodziny {self.rodzina.nazwa}",
        )

        self.czlonek.delete()
        messages.success(
            request,
            f"Osoba {osoba_txt} została usunięta z tej rodziny.",
        )
        return redirect(self.rodzina.get_absolute_url())


class CzlonkostwoUsunView(RolaWymaganaMixin, DeleteView):
    """
    Klasyczny DeleteView dla CzlonkostwoRodziny (gdy nie używamy wariantu z rodzina_pk).
    """
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = CzlonkostwoRodziny
    template_name = "rodziny/czlonek_usun.html"
    context_object_name = "czlonkostwo"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        zapisz_log(
            request,
            "USUNIECIE_CZLONKA_RODZINY",
            self.object,
            opis=(
                f"Usunięto członka rodziny: {self.object.osoba} "
                f"z rodziny {self.object.rodzina.nazwa}"
            ),
        )

        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Osoba została usunięta z rodziny.")
        return self.object.rodzina.get_absolute_url()
