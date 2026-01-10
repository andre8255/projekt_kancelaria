# msze/views.py
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
    FormView,
)

from parafia.utils_pdf import render_to_pdf

from konta.mixins import RolaWymaganaMixin
from konta.models import Rola
from konta.utils import zapisz_log

from .forms import MszaForm, IntencjaForm
from .models import Msza, IntencjaMszy, TypMszy


# =============================================================================
#  LISTA / FILTROWANIE MSZY
# =============================================================================
class MszaListaView(LoginRequiredMixin, ListView):
    model = Msza
    template_name = "msze/lista_mszy.html"
    context_object_name = "msze"
    paginate_by = 50

    def get_queryset(self):
        """
        Podstawowa lista mszy z filtrami:
        - zakres dat (data_od, data_do)
        - typ mszy
        - status (wolna/zajeta)
        - wyszukiwarka tekstowa (miejsce, nazwisko celebransa)
        """
        qs = Msza.objects.all().order_by("data", "godzina")

        # --- 1. Filtr zakresu dat (OD - DO) ---
        data_od = self.request.GET.get("data_od")
        data_do = self.request.GET.get("data_do")

        if data_od:
            qs = qs.filter(data__gte=data_od)

        if data_do:
            qs = qs.filter(data__lte=data_do)

        # --- 2. Filtr Typu Mszy ---
        typ = self.request.GET.get("typ")
        if typ:
            qs = qs.filter(typ=typ)

        # --- 3. Filtr Statusu (Wolna/Zajęta) ---
        qs = qs.annotate(
            zajeta=Exists(IntencjaMszy.objects.filter(msza=OuterRef("pk")))
        )
        status = (self.request.GET.get("status") or "").lower().strip()
        if status == "wolna":
            qs = qs.filter(zajeta=False)
        elif status == "zajeta":
            qs = qs.filter(zajeta=True)

        # --- 4. Wyszukiwarka tekstowa ---
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(miejsce__icontains=q)
                | Q(celebrans__imie_nazwisko__icontains=q)
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # typy mszy do selecta
        ctx["typy_mszy"] = TypMszy.choices

        # aktualne filtry, żeby zostawały w formularzu
        ctx["filtr_data_od"] = self.request.GET.get("data_od", "")
        ctx["filtr_data_do"] = self.request.GET.get("data_do", "")
        ctx["filtr_typ"] = self.request.GET.get("typ", "")
        ctx["filtr_status"] = self.request.GET.get("status", "")
        ctx["filtr_q"] = self.request.GET.get("q", "")
        return ctx


# =============================================================================
#  CRUD MSZY
# =============================================================================
class MszaNowaView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Msza
    form_class = MszaForm
    template_name = "msze/msza_formularz.html"

    def get_initial(self):
        """
        Jeśli przyszliśmy z kalendarza (?data=2025-01-01T18:00:00)
        – wstępnie uzupełnij datę/godzinę.
        """
        initial = super().get_initial()
        data_str = self.request.GET.get("data")

        if data_str:
            klikniety_czas = parse_datetime(data_str)
            if klikniety_czas:
                initial["data"] = klikniety_czas.date()
                initial["godzina"] = klikniety_czas.time()
            else:
                kliknieta_data = parse_date(data_str)
                if kliknieta_data:
                    initial["data"] = kliknieta_data

        return initial

    def form_valid(self, form):
        response = super().form_valid(form)

        zapisz_log(
            self.request,
            "DODANIE_MSZY",
            self.object,
            opis=f"Dodano mszę: {self.object.data} "
                 f"{self.object.godzina} w {self.object.miejsce}",
        )

        messages.success(self.request, "Dodano nową mszę.")
        return response

    def get_success_url(self):
        return reverse("msza_lista")


class MszaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Msza
    form_class = MszaForm
    template_name = "msze/msza_formularz.html"
    success_url = reverse_lazy("msza_lista")

    def form_valid(self, form):
        response = super().form_valid(form)

        zapisz_log(
            self.request,
            "EDYCJA_MSZY",
            self.object,
            opis=f"Zmieniono mszę: {self.object.data} "
                 f"{self.object.godzina} w {self.object.miejsce}",
        )

        messages.success(self.request, "Zapisano zmiany przy mszy.")
        return response


class MszaSzczegolyView(LoginRequiredMixin, DetailView):
    model = Msza
    template_name = "msze/msza_szczegoly.html"
    context_object_name = "msza"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        msza = self.object
        ctx["intencje"] = msza.intencje.all()
        return ctx


class MszaUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = Msza
    template_name = "msze/msza_usun.html"
    success_url = reverse_lazy("msza_lista")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        zapisz_log(
            request,
            "USUNIECIE_MSZY",
            self.object,
            opis=f"Usunięto mszę: {self.object.data} "
                 f"{self.object.godzina} w {self.object.miejsce}",
        )

        messages.success(request, "Msza została usunięta.")
        return super().delete(request, *args, **kwargs)


# =============================================================================
#  LISTA / DRUK / PDF
# =============================================================================
class MszaListaDrukView(MszaListaView):
    """
    Widok do wydruku (HTML) – bez paginacji, z prefetch intencji.
    """
    template_name = "msze/druki/msza_lista_druk.html"
    paginate_by = None

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("intencje")


class MszaListaPDFView(MszaListaView):
    """
    Generuje PDF z listy mszy, zachowując aktywne filtry (data, status, typ).
    """
    def render_to_response(self, context, **response_kwargs):
        context["today"] = timezone.now()
        filename = f"Wykaz_Mszy_{timezone.localdate()}.pdf"
        return render_to_pdf("msze/druki/msza_lista_pdf.html", context, filename)


# =============================================================================
#  INTENCJE
# =============================================================================
class IntencjaNowaView(RolaWymaganaMixin, FormView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    template_name = "msze/intencja_formularz.html"
    form_class = IntencjaForm

    def dispatch(self, request, *args, **kwargs):
        self.msza = get_object_or_404(Msza, pk=kwargs["msza_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        intencja = form.save(commit=False)
        intencja.msza = self.msza
        intencja.save()

        zapisz_log(
            self.request,
            "DODANIE_INTENCJI",
            intencja,
            opis=(
                f"Dodano intencję do mszy {self.msza.data} "
                f"{self.msza.godzina}: {intencja.tresc[:10]}"
            ),
        )

        messages.success(self.request, "Dodano intencję do tej mszy.")
        return redirect(self.msza.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["msza"] = self.msza
        return ctx


class IntencjaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = IntencjaMszy
    form_class = IntencjaForm
    template_name = "msze/intencja_formularz.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["msza"] = self.object.msza
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)

        zapisz_log(
            self.request,
            "EDYCJA_INTENCJI",
            self.object,
            opis=(
                f"Zmieniono intencję dla mszy "
                f"{self.object.msza.data} {self.object.msza.godzina}"
            ),
        )

        messages.success(self.request, "Zapisano zmiany intencji.")
        return response

    def get_success_url(self):
        return self.object.msza.get_absolute_url()


class IntencjaUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIADZ]
    model = IntencjaMszy
    template_name = "msze/intencja_usun.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        zapisz_log(
            request,
            "USUNIECIE_INTENCJI",
            self.object,
            opis=(
                f"Usunięto intencję dla mszy "
                f"{self.object.msza.data} {self.object.msza.godzina}"
            ),
        )

        messages.success(request, "Intencja została usunięta.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.msza.get_absolute_url()


# =============================================================================
#  KALENDARZ
# =============================================================================
class KalendarzMszyView(LoginRequiredMixin, TemplateView):
    template_name = "msze/kalendarz.html"


def kalendarz_mszy_dane(request):
    """
    Zwraca listę wydarzeń dla FullCalendar z uwzględnieniem kolorów typów mszy
    i informacją czy msza ma intencje.
    """
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")

    def parse_iso(dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            # FullCalendar podaje np. '2025-01-01T00:00:00Z'
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    start_dt = parse_iso(start_str)
    end_dt = parse_iso(end_str)

    today = timezone.localdate()
    msze_qs = (
        Msza.objects
        .filter(data__gte=today)
        .order_by("data", "godzina")
        .prefetch_related("intencje")
    )

    if start_dt and end_dt:
        msze_qs = msze_qs.filter(
            data__gte=start_dt.date(),
            data__lte=end_dt.date(),
        )

    events = []
    for msza in msze_qs:
        dt = datetime.combine(msza.data, msza.godzina)
        has_intencje = msza.intencje.exists()

        # 1. Tytuł wydarzenia
        if has_intencje:
            tresci = list(msza.intencje.values_list("tresc", flat=True))
            tytul = " • ".join(tresci)
        else:
            # jeśli nie ma intencji – pokazujemy typ mszy
            tytul = f"{msza.get_typ_display()} - wolna"

        # 2. Kolor
        if msza.typ == TypMszy.POWSZEDNIA and has_intencje:
            # powszednia + zajęta = pomarańcz
            kolor = "#fd7e14"
        else:
            # inne bierzemy z metody modelu
            kolor = msza.get_kolor_kalendarza()

        events.append(
            {
                "title": tytul,
                "start": dt.isoformat(),
                "url": msza.get_absolute_url(),
                "color": kolor,
                "borderColor": (
                    "#000" if not has_intencje and msza.typ != TypMszy.POWSZEDNIA else kolor
                ),
                "extendedProps": {
                    "isBusy": has_intencje,  # True jeśli są intencje
                },
            }
        )

    return JsonResponse(events, safe=False)
