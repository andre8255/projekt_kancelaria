from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.contrib import messages
from datetime import datetime, time
from django.views.generic import TemplateView, DeleteView
from datetime import date
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Exists, OuterRef,Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, FormView
)

from .models import Msza, IntencjaMszy
from .forms import MszaForm, IntencjaForm

class MszaListaView(LoginRequiredMixin, ListView):
    model = Msza
    template_name = "msze/lista_mszy.html"
    context_object_name = "msze"
    paginate_by = 50

    def get_queryset(self):
        qs = Msza.objects.all().order_by("data", "godzina")

        # Pokaż tylko dzisiejsze i przyszłe (jeśli tak chcesz)
        qs = qs.filter(data__gte=timezone.localdate())

        # Adnotacja: czy msza ma jakąkolwiek intencję
        qs = qs.annotate(
            zajeta=Exists(
                IntencjaMszy.objects.filter(msza=OuterRef("pk"))
            )
        )
        # --- filtr po dacie (YYYY-MM-DD z <input type="date">) ---
        data_str = (self.request.GET.get("data") or "").strip()
        if data_str:
            d = parse_date(data_str)
            if d:
                qs = qs.filter(data=d)


        # Filtr: wolna / zajeta
        status = (self.request.GET.get("status") or "").lower().strip()
        if status == "wolna":
            qs = qs.filter(zajeta=False)
        elif status == "zajeta":
            qs = qs.filter(zajeta=True)

        # Prosty search (miejsce / celebrans)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(miejsce__icontains=q) | Q(celebrans__icontains=q))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtr_data"] = self.request.GET.get("data", "")
        ctx["filtr_status"] = self.request.GET.get("status", "")
        ctx["filtr_q"] = self.request.GET.get("q", "")
        return ctx
    
class MszaNowaView(LoginRequiredMixin, CreateView):
    model = Msza
    form_class = MszaForm
    template_name = "msze/msza_formularz.html"
    success_url = reverse_lazy("msza_lista")

class MszaEdycjaView(LoginRequiredMixin, UpdateView):
    model = Msza
    form_class = MszaForm
    template_name = "msze/msza_formularz.html"
    success_url = reverse_lazy("msza_lista")


class MszaSzczegolyView(LoginRequiredMixin, DetailView):
    model = Msza
    template_name = "msze/msza_szczegoly.html"
    context_object_name = "msza"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        msza = self.object
        ctx["intencje"] = msza.intencje.all()
        return ctx
    
class MszaUsunView(LoginRequiredMixin, DeleteView):
    model = Msza
    template_name = "msze/msza_usun.html"   # patrz pkt 3
    success_url = reverse_lazy("msza_lista")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Msza została usunięta.")
        return super().delete(request, *args, **kwargs)

class IntencjaNowaView(LoginRequiredMixin, FormView):
    template_name = "msze/intencja_formularz.html"
    form_class = IntencjaForm

    def dispatch(self, request, *args, **kwargs):
        self.msza = get_object_or_404(Msza, pk=kwargs["msza_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        intencja = form.save(commit=False)
        intencja.msza = self.msza
        intencja.save()
        messages.success(self.request, "Dodano intencję do tej mszy.")
        return redirect(self.msza.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["msza"] = self.msza
        return ctx

class IntencjaEdycjaView(LoginRequiredMixin, UpdateView):
    model = IntencjaMszy
    form_class = IntencjaForm
    template_name = "msze/intencja_formularz.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["msza"] = self.object.msza          # <-- żeby szablon miał msza.pk także przy edycji
        return ctx
    
    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany intencji.")
        return self.object.msza.get_absolute_url()

class IntencjaUsunView(LoginRequiredMixin, DeleteView):
    model = IntencjaMszy
    template_name = "msze/intencja_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Intencja została usunięta.")
        return self.object.msza.get_absolute_url()


class KalendarzMszyView(LoginRequiredMixin, TemplateView):
    template_name = "msze/kalendarz.html"


def kalendarz_mszy_dane(request):
    """
    Zwraca listę wydarzeń dla FullCalendar.
    Tytuł = złączone treści intencji (lub 'wolna' gdy brak).
    Pokazuje tylko msze dzisiejsze i przyszłe.
    Uwzględnia opcjonalne GET:start / GET:end wysyłane przez FullCalendar.
    """
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")

    def parse_iso(dt_str):
        if not dt_str:
            return None
        try:
            # FullCalendar wysyła ISO 8601, często z 'Z'
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    start_dt = parse_iso(start_str)
    end_dt = parse_iso(end_str)

    # bazowy queryset: tylko msze dziś i w przyszłości
    today = timezone.localdate()
    msze_qs = (
        Msza.objects
        .filter(data__gte=today)
        .order_by("data", "godzina")
        .prefetch_related("intencje")
    )

    # jeśli FullCalendar poda zakres – zawężamy dodatkowo
    if start_dt and end_dt:
        msze_qs = msze_qs.filter(
            data__gte=start_dt.date(),
            data__lte=end_dt.date()
        )

    events = []
    for msza in msze_qs:
        dt = datetime.combine(msza.data, msza.godzina)

        if msza.intencje.exists():
            tresci = list(msza.intencje.values_list("tresc", flat=True))
            tytul = " • ".join(tresci)
            kolor = "#dc3545"   # zajęta
        else:
            tytul = "wolna"
            kolor = "#198754"   # wolna

        events.append({
            "title": tytul,
            "start": dt.isoformat(),   # np. "2025-11-02T18:00:00"
            "url": msza.get_absolute_url(),
            "color": kolor,
        })

    return JsonResponse(events, safe=False)