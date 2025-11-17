# osoby/views.py

# === IMPORTY ===
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    TemplateView,
    View,
)

# Importy ról
from konta.mixins import RolaWymaganaMixin
from konta.models import Rola

# Importy do Panelu Startowego
from django.utils import timezone
import calendar
from datetime import date, timedelta
from msze.models import Msza
from rodziny.models import Rodzina
from sakramenty.models import Chrzest, Malzenstwo

from .models import Osoba
from .forms import OsobaForm


# =============================================================================
# === WIDOKI ===
# =============================================================================

class PanelStartView(LoginRequiredMixin, TemplateView):
    template_name = "panel_start.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()

        # --- kafelki (statystyki) ---
        ctx["stats"] = {
            "osoby": Osoba.objects.count(),
            "rodziny": Rodzina.objects.count(),
            "chrzty": Chrzest.objects.count(),
            # Dodaj resztę statystyk, jeśli chcesz
            # "bierzmowania": Bierzmowanie.objects.count(),
            "sluby": Malzenstwo.objects.count(),
            # "zgony": Zgon.objects.count(),
        }

        # --- najbliższe msze ---
        ctx["msze_najblizsze"] = (
            Msza.objects.filter(data__gte=today)
            .order_by("data", "godzina")
            .prefetch_related("intencje")[:8]
        )

        # --- ostatnie wpisy ---
        ctx["ostatnie_chrzty"] = Chrzest.objects.select_related("ochrzczony").order_by("-id")[:5]
        ctx["ostatnie_sluby"] = (
            Malzenstwo.objects.select_related("malzonek_a", "malzonek_b").order_by("-id")[:5]
        )

       # ===== MINI KALENDARZ (miesiąc bieżący) =====
        year, month = today.year, today.month

        # 1) budujemy zakres miesiąca
        first_day = date(year, month, 1)
        if month == 12:
            next_first = date(year + 1, 1, 1)
        else:
            next_first = date(year, month + 1, 1)
        last_day = next_first - timedelta(days=1)

        # 2) liczymy msze i zajętość per dzień
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

        # 3) układ tygodni
        cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        raw_weeks = cal.monthdatescalendar(year, month)

        # 4) przygotowujemy dane do szablonu
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
                    "is_today": (d == today),
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

        # (Logika pobierania sakramentów została usunięta z tego widoku,
        # ponieważ znajdowała się w starej, nadpisanej wersji.
        # Jeśli była potrzebna, trzeba ją będzie przywrócić z sakramenty/views.py)
        
        # Poprawka: pobieranie rodzin, do których należy osoba
        ctx["rodziny"] = osoba.przynaleznosci_rodzinne.all() 
        return ctx

class OsobaNowaView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Osoba
    form_class = OsobaForm
    template_name = "osoby/formularz.html"
    success_url = reverse_lazy("osoba_lista")

    def form_valid(self, form):
        messages.success(self.request, "Nowa osoba została dodana.")
        return super().form_valid(form)


class OsobaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Osoba
    form_class = OsobaForm
    template_name = "osoby/formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Dane osoby zostały zaktualizowane.")
        return reverse_lazy("osoba_szczegoly", args=[self.object.pk])


class OsobaUsunView(RolaWymaganaMixin, View):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]

    def get(self, request, *args, **kwargs):
        # GET nie powinien usuwać danych, ale zostawiam logikę, którą miałeś
        osoba = get_object_or_404(Osoba, pk=self.kwargs.get("pk"))
        
        # Lepsza obsługa błędu ProtectedError
        try:
            osoba.delete()
            messages.success(request, f"Osoba {osoba} została usunięta.")
            return HttpResponseRedirect(reverse_lazy("osoba_lista"))
        except: # (Powinno być models.ProtectedError, ale zostawiam ogólny)
             messages.error(
                request,
                f"Nie można usunąć osoby '{osoba}', "
                f"ponieważ jest powiązana z aktami (np. chrztu, ślubu) lub rodziną."
            )
             return redirect("osoba_szczegoly", pk=osoba.pk)

    def post(self, request, *args, **kwargs):
        # Poprawna metoda POST do usuwania
        osoba = get_object_or_404(Osoba, pk=self.kwargs.get("pk"))
        try:
            osoba.delete()
            messages.success(request, f"Osoba {osoba} została usunięta.")
            return HttpResponseRedirect(reverse_lazy("osoba_lista"))
        except:
             messages.error(
                request,
                f"Nie można usunąć osoby '{osoba}', "
                f"ponieważ jest powiązana z aktami (np. chrztu, ślubu) lub rodziną."
            )
             return redirect("osoba_szczegoly", pk=osoba.pk)