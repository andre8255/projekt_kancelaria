# osoby/views.py

# === IMPORTY ===
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from parafia.utils_pdf import render_to_pdf
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    TemplateView,
    View,
)
from konta.models import BackupUstawienia
from konta.utils_backup import czy_backup_jest_nalezny, wykonaj_backup_bazy
from konta.utils import zapisz_log
from django.db.models.deletion import ProtectedError
from cmentarz.models import Grob

# Importy ról
from konta.mixins import RolaWymaganaMixin
from konta.models import Rola

# Importy do Panelu Startowego
from django.utils import timezone
import calendar
from datetime import date, timedelta
from msze.models import Msza
from rodziny.models import Rodzina

# Importy sakramentów (potrzebne do OsobaSzczegolyView)
from sakramenty.models import (
    Chrzest,
    PierwszaKomunia,
    Bierzmowanie,
    Malzenstwo,
    NamaszczenieChorych,
    Zgon
)

from .models import Osoba
from .forms import OsobaForm


# =============================================================================
# === WIDOKI ===
# =============================================================================

# osoby/views.py

class PanelStartView(LoginRequiredMixin, TemplateView):
    template_name = "panel_start.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today_real = timezone.localdate()

        # --- STATYSTYKI ---
        ctx["stats"] = {
            "osoby": Osoba.objects.count(),
            "rodziny": Rodzina.objects.count(),
            "chrzty": Chrzest.objects.count(),
            "bierzmowania": Bierzmowanie.objects.count(),
            "sluby": Malzenstwo.objects.count(),
            "groby": Grob.objects.count(), # Dodano licznik grobów
        }
        
        # --- POWIADOMIENIA O GROBACH (NAPRAWIONE) ---
        # Szukamy grobów, których ważność minęła (wazny_do < dzis)
        ctx["groby_po_terminie"] = Grob.objects.filter(
            wazny_do__isnull=False,
            wazny_do__lt=today_real
        ).count()

        # --- NAJBLIŻSZE MSZE ---
        ctx["msze_najblizsze"] = (
            Msza.objects.filter(data__gte=today_real)
            .order_by("data", "godzina")
            .prefetch_related("intencje")[:8]
        )

        # === ALERTY CMENTARZA ===
        today = timezone.localdate()
        six_months = today + timedelta(days=180)

        groby_po_terminie = Grob.objects.filter(
            wazny_do__isnull=False,
            wazny_do__lt=today,
        ).order_by("wazny_do")

        groby_6_miesiecy = Grob.objects.filter(
            wazny_do__isnull=False,
            wazny_do__gte=today,
            wazny_do__lte=six_months,
        ).order_by("wazny_do")

        ctx["groby_po_terminie"] = groby_po_terminie[:5]
        ctx["groby_6_miesiecy"] = groby_6_miesiecy[:5]

        ctx["cmentarz_alert"] = {
            "po_terminie": groby_po_terminie.count(),
            "do_6_miesiecy": groby_6_miesiecy.count(),
            "lacznie": groby_po_terminie.count() + groby_6_miesiecy.count(),
        }

        # ===== MINI KALENDARZ =====
        # 1. Parametry
        req_year = self.request.GET.get("year")
        req_month = self.request.GET.get("month")

        try:
            if req_year and req_month:
                year = int(req_year)
                month = int(req_month)
                if month < 1 or month > 12: raise ValueError
            else:
                year, month = today_real.year, today_real.month
        except (ValueError, TypeError):
            year, month = today_real.year, today_real.month

        # 2. Nawigacja
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
        
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

        ctx["nav_prev"] = f"?year={prev_year}&month={prev_month}"
        ctx["nav_next"] = f"?year={next_year}&month={next_month}"
        ctx["nav_current"] = f"?year={today_real.year}&month={today_real.month}"

        # 3. Zakres dat
        first_day = date(year, month, 1)
        next_month_first = date(next_year, next_month, 1)
        last_day = next_month_first - timedelta(days=1)

        # 4. Dane
        msze = (
            Msza.objects.filter(data__gte=first_day, data__lte=last_day)
            .order_by("data", "godzina")
            .prefetch_related("intencje")
        )
        counts = {}
        for m in msze:
            rec = counts.setdefault(m.data, {"all": 0, "busy": 0})
            rec["all"] += 1
            if m.intencje.exists():
                rec["busy"] += 1

        # 5. Kalendarz
        cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        raw_weeks = cal.monthdatescalendar(year, month)

        weeks_data = []
        for week in raw_weeks:
            row = []
            for d in week:
                c = counts.get(d, {"all": 0, "busy": 0})
                row.append({
                    "date": d,
                    "is_other_month": (d.month != month),
                    "all": c["all"],
                    "busy": c["busy"],
                    "is_today": (d == today_real),
                })
            weeks_data.append(row)

        PL_MIESIACE = [
            "", "styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec",
            "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień"
        ]

        ctx["mini_kalendarz"] = {
            "weeks": weeks_data,
            "month_label": f"{PL_MIESIACE[month]} {year}",
        }
        ctx["dni_tyg"] = ["pn", "wt", "śr", "czw", "pt", "sob", "nd"]

        return ctx


class OsobaListaView(LoginRequiredMixin, ListView):
    model = Osoba
    template_name = "osoby/lista.html"
    context_object_name = "osoby"
    paginate_by = 20

    def get_queryset(self):
        qs = Osoba.objects.all().order_by("nazwisko", "imie_pierwsze", "pk")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            for slowo in q.split():
                qs = qs.filter(
                    Q(nazwisko__icontains=slowo) |
                    Q(imie_pierwsze__icontains=slowo) |
                    Q(nazwisko_rodowe__icontains=slowo)
                )
        return qs

class OsobaSzczegolyView(LoginRequiredMixin, DetailView):
    model = Osoba
    template_name = "osoby/szczegoly.html"
    context_object_name = "osoba"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        osoba = self.object

        # --- PRZYWRÓCONA LOGIKA POBIERANIA SAKRAMENTÓW ---

        # 1. Chrzty
        ctx["chrzty_osoby"] = (
            Chrzest.objects.filter(ochrzczony=osoba)
            .order_by("rok", "akt_nr")
        )

        # 2. I Komunia
        ctx["komunia_osoby"] = (
            PierwszaKomunia.objects.filter(osoba=osoba)
            .first()
        )

        # 3. Bierzmowanie
        ctx["bierzmowanie_osoby"] = (
            Bierzmowanie.objects.filter(osoba=osoba)
            .order_by("rok", "akt_nr")
            .first()
        )

        # 4. Małżeństwa (jako mąż lub żona)
        ctx["malzenstwa_osoby"] = (
            Malzenstwo.objects.filter(
                Q(malzonek_a=osoba) | Q(malzonek_b=osoba)
            ).order_by("rok", "akt_nr")
        )

        # 5. Namaszczenia
        ctx["namaszczenia_osoby"] = (
            NamaszczenieChorych.objects.filter(osoba=osoba)
            .order_by("-data")
        )

        # 6. Zgon (OneToOne, więc dostęp przez atrybut, ale bezpiecznie sprawdzamy)
        ctx["zgon_osoby"] = getattr(osoba, "zgon", None)

        # 7. Rodziny
        ctx["rodziny"] = osoba.przynaleznosci_rodzinne.all() 
        
        return ctx

class OsobaNowaView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Osoba
    form_class = OsobaForm
    template_name = "osoby/formularz.html"
    success_url = reverse_lazy("osoba_lista")

    def form_valid(self, form):
        response = super().form_valid(form)
        zapisz_log(
            self.request,
            "DODANIE_OSOBY",
            self.object,
            opis=f"Dodano osobę: {self.object.imie_pierwsze} {self.object.nazwisko}"
        )
        return response


class OsobaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Osoba
    form_class = OsobaForm
    template_name = "osoby/formularz.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        zapisz_log(
            self.request,
            "EDYCJA_OSOBY",
            self.object,
            opis=f"Zmieniono dane osoby: {self.object.imie_pierwsze} {self.object.nazwisko}"
        )
        return response

    def get_success_url(self):
        messages.success(self.request, "Dane osoby zostały zaktualizowane.")
        return reverse_lazy("osoba_szczegoly", args=[self.object.pk])


class OsobaUsunView(RolaWymaganaMixin, View):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    template_name = "osoby/osoba_usun.html"

    def get_object(self):
        return get_object_or_404(Osoba, pk=self.kwargs.get("pk"))

    def get(self, request, *args, **kwargs):
        osoba = self.get_object()
        # TYLKO pokazujemy stronę z pytaniem
        return render(request, self.template_name, {"object": osoba})

    def post(self, request, *args, **kwargs):
        osoba = self.get_object()
        try:
            osoba.delete()
        except ProtectedError:
            messages.error(
                request,
                f"Nie można usunąć osoby '{osoba}', "
                f"ponieważ jest powiązana z aktami (np. chrztu, ślubu) lub rodziną."
            )
            return redirect("osoba_szczegoly", pk=osoba.pk)
        else:
            zapisz_log(
                request,
                "USUNIECIE_OSOBY",
                osoba,
                opis=f"Usunięto osobę: {osoba.imie_pierwsze} {osoba.nazwisko}"
            )
            messages.success(request, f"Osoba {osoba} została usunięta.")
            return redirect("osoba_lista")

        

class GlobalSearchView(LoginRequiredMixin, TemplateView):
    template_name = "szukaj_globalnie.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        ctx["q"] = q

        if not q:
            ctx["wyniki_osoby"] = []
            ctx["wyniki_rodziny"] = []
            ctx["wyniki_chrzty"] = []
            ctx["wyniki_sluby"] = []
            return ctx

        # Osoby
        ctx["wyniki_osoby"] = Osoba.objects.filter(
            Q(imie_pierwsze__icontains=q) |
            Q(imie_drugie__icontains=q) |
            Q(nazwisko__icontains=q) |
            Q(nazwisko_rodowe__icontains=q)
        )[:20]

        # Rodziny
        ctx["wyniki_rodziny"] = Rodzina.objects.filter(
            Q(nazwa__icontains=q) |
            Q(ulica__icontains=q) |
            Q(miejscowosc__icontains=q)
        )[:20]

        # Chrzty
        ctx["wyniki_chrzty"] = Chrzest.objects.select_related("ochrzczony").filter(
            Q(ochrzczony__nazwisko__icontains=q) |
            Q(ochrzczony__imie_pierwsze__icontains=q) |
            Q(akt_nr__icontains=q)
        )[:20]

        # Małżeństwa
        ctx["wyniki_sluby"] = Malzenstwo.objects.select_related(
            "malzonek_a", "malzonek_b"
        ).filter(
            Q(malzonek_a__nazwisko__icontains=q) |
            Q(malzonek_b__nazwisko__icontains=q)
        )[:20]

        return ctx

class OsobaPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        osoba = get_object_or_404(Osoba, pk=kwargs['pk'])

        # ... (reszta pobierania danych bez zmian) ...
        chrzty = Chrzest.objects.filter(ochrzczony=osoba)
        komunie = PierwszaKomunia.objects.filter(osoba=osoba)
        bierzmowania = Bierzmowanie.objects.filter(osoba=osoba)
        malzenstwa = Malzenstwo.objects.filter(
            Q(malzonek_a=osoba) | Q(malzonek_b=osoba)
        ).select_related("malzonek_a", "malzonek_b", "parafia")
        namaszczenia = NamaszczenieChorych.objects.filter(osoba=osoba).order_by('-data')
        zgon = Zgon.objects.filter(osoba=osoba).first()

        context = {
            'osoba': osoba,
            'chrzty': chrzty,
            'komunie': komunie,
            'bierzmowania': bierzmowania,
            'malzenstwa': malzenstwa,
            'namaszczenia': namaszczenia,
            'zgon_osoby': zgon,
            
            # --- TU BYŁ BŁĄD ---
            # Było: 'today': timezone.localdate(),  <- to jest sama data (bez godziny)
            # Jest:
            'today': timezone.now(),              # <- to jest data i czas
        }

        safe_name = "".join([c if c.isalnum() else "_" for c in f"{osoba.nazwisko}_{osoba.imie_pierwsze}"])
        filename = f"Kartoteka_Osobowa_{safe_name}.pdf"

        return render_to_pdf('osoby/druki/osoba_pdf.html', context, filename)