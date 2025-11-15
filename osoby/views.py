# osoby/views.py
from django.utils import timezone
from django.db import models
from django.contrib import messages
from .models import Osoba
from .forms import OsobaForm
from django.views.generic import TemplateView
from django.views import View
from django.db.models import Q
from django.views.generic import TemplateView
from msze.models import Msza
from osoby.models import Osoba
from rodziny.models import Rodzina
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.db.models.deletion import ProtectedError
from django.contrib.auth.mixins import LoginRequiredMixin
import calendar
from datetime import date, timedelta

from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from sakramenty.models import (
    Chrzest,
    PierwszaKomunia,
    Bierzmowanie,
    Malzenstwo,
    NamaszczenieChorych,
    Zgon,
)




class PanelStartView(TemplateView):
    template_name = "panel_start.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()

        # --- kafelki ---
        ctx["stats"] = {
            "osoby": Osoba.objects.count(),
            "rodziny": Rodzina.objects.count() if "Rodzina" in globals() else 0,
            "chrzty": Chrzest.objects.count(),
            "bierzmowania": Bierzmowanie.objects.count(),
            "sluby": Malzenstwo.objects.count(),
            "zgony": Zgon.objects.count(),
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

        # 3) układ tygodni – UWAGA: to jest metoda obiektu Calendar
        cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        raw_weeks = cal.monthdatescalendar(year, month)  # <-- tu był błąd

        # 4) przygotowujemy „przyjazne” dane do szablonu
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
            "weeks": weeks_data,                 # lista tygodni; każdy to lista słowników
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

        # Wszystkie chrzty tej osoby (raczej będzie 1, ale pozwalamy na więcej)
        ctx["chrzty_osoby"] = (
            Chrzest.objects.filter
            (ochrzczony=osoba)
            .order_by("rok", "akt_nr")
        )

        # Pierwsza Komunia – zakładamy pojedynczy wpis
        ctx["komunia_osoby"] = (
            PierwszaKomunia.objects
            .filter(osoba=osoba)
            .order_by("rok")
            .first()
        )

        # Bierzmowanie – zakładamy pojedynczy wpis
        ctx["bierzmowanie_osoby"] = (
            Bierzmowanie.objects
            .filter(osoba=osoba)
            .order_by("rok", "akt_nr")
            .first()
        )

        # Małżeństwa – może być kilka (wdowiec/wdowa, ponowne)
        ctx["malzenstwa_osoby"] = (
            Malzenstwo.objects.filter(
                models.Q(malzonek_a=osoba) | models.Q(malzonek_b=osoba)
            ).order_by("rok", "akt_nr")
        )

        # Namaszczenie chorych / posługi do chorych – może być wiele
        ctx["namaszczenia_osoby"] = (
            NamaszczenieChorych.objects
            .filter(osoba=osoba)
            .order_by("-data")
        )

        # Zgon – jeden wpis max
        ctx["zgon_osoby"] = getattr(osoba, "zgon", None)

        return ctx

class OsobaNowaView(LoginRequiredMixin, CreateView):
    model = Osoba
    form_class = OsobaForm
    template_name = "osoby/formularz.html"
    success_url = reverse_lazy("osoba_lista")

class OsobaEdycjaView(LoginRequiredMixin, UpdateView):
    model = Osoba
    form_class = OsobaForm
    template_name = "osoby/formularz.html"
    success_url = reverse_lazy("osoba_lista")
    
class OsobaUsunView(LoginRequiredMixin, View):
    template_name = "osoby/osoba_usun.html"

    def get(self, request, pk):
        osoba = get_object_or_404(Osoba, pk=pk)
        return render(request, self.template_name, {"object": osoba})

    def post(self, request, pk):
        osoba = get_object_or_404(Osoba, pk=pk)

        try:
            osoba.delete()  # próbujemy usunąć normalnie
            messages.success(request, "Osoba została usunięta.")
            return redirect("osoba_lista")

        except ProtectedError:
            # <-- TO jest ten przypadek, który właśnie widziałeś
            messages.error(
                request,
                "Nie można usunąć tej osoby, bo jest powiązana w aktach lub kartotece."
            )
            # wracamy do szczegółów osoby
            return redirect("osoba_szczegoly", pk=osoba.pk)
