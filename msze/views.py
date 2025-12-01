# msze/views.py
from django.utils.dateparse import parse_datetime, parse_date
from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.urls import reverse
from django.contrib import messages
from datetime import datetime, time
from django.views.generic import TemplateView, DeleteView
from datetime import date
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Exists, OuterRef,Q
from django.contrib.auth.mixins import LoginRequiredMixin
from parafia.utils_pdf import render_to_pdf
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, FormView
)

# Importy ról
from konta.mixins import RolaWymaganaMixin
from konta.models import Rola
from konta.utils import zapisz_log

from .models import Msza, IntencjaMszy, TypMszy
from .forms import MszaForm, IntencjaForm

class MszaListaView(LoginRequiredMixin, ListView):
    model = Msza
    template_name = "msze/lista_mszy.html"
    context_object_name = "msze"
    paginate_by = 50

    def get_queryset(self):
        # Domyślne sortowanie: od najnowszych (żeby widzieć nadchodzące/ostatnie na górze)
        # lub "data", "godzina" jeśli wolisz chronologicznie rosnąco.
        qs = Msza.objects.all().order_by("data", "godzina")

        # --- 1. Filtr zakresu dat (OD - DO) ---
        data_od = self.request.GET.get("data_od")
        data_do = self.request.GET.get("data_do")

        if data_od:
            qs = qs.filter(data__gte=data_od)
        else:
            # Opcjonalnie: jeśli nie wybrano daty OD, pokaż tylko przyszłe (jak było wcześniej)
            # Ale przy wyszukiwarce lepiej domyślnie pokazać np. bieżący rok lub wszystko.
            # Tutaj zostawiamy "wszystko" lub filtr z poprzedniej logiki:
            # qs = qs.filter(data__gte=timezone.localdate()) 
            pass

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

        # --- 4. Szukajka tekstowa ---
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(miejsce__icontains=q) | Q(celebrans__imie_nazwisko__icontains=q))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Przekazujemy opcje do selecta w szablonie
        ctx["typy_mszy"] = TypMszy.choices
        
        # Zachowujemy wartości filtrów w formularzu
        ctx["filtr_data_od"] = self.request.GET.get("data_od", "")
        ctx["filtr_data_do"] = self.request.GET.get("data_do", "")
        ctx["filtr_typ"] = self.request.GET.get("typ", "")
        ctx["filtr_status"] = self.request.GET.get("status", "")
        ctx["filtr_q"] = self.request.GET.get("q", "")
        return ctx
    
class MszaNowaView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
    model = Msza
    form_class = MszaForm
    template_name = "msze/msza_formularz.html"

    def get_initial(self):
        initial = super().get_initial()
        data_str = self.request.GET.get('data')

        if data_str:
            klikniety_czas = parse_datetime(data_str)
            if klikniety_czas:
                initial['data'] = klikniety_czas.date()
                initial['godzina'] = klikniety_czas.time()
            else:
                kliknieta_data = parse_date(data_str)
                if kliknieta_data:
                    initial['data'] = kliknieta_data
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)

        zapisz_log(
            self.request,
            "DODANIE_MSZY",
            self.object,
            opis=f"Dodano mszę: {self.object.data} {self.object.godzina} w {self.object.miejsce}"
        )

        messages.success(self.request, "Dodano nową mszę.")
        return response

    def get_success_url(self):
        return reverse('msza_lista')



class MszaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
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
            opis=f"Zmieniono mszę: {self.object.data} {self.object.godzina} w {self.object.miejsce}"
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
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Msza
    template_name = "msze/msza_usun.html"
    success_url = reverse_lazy("msza_lista")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        zapisz_log(
            request,
            "USUNIECIE_MSZY",
            self.object,
            opis=f"Usunięto mszę: {self.object.data} {self.object.godzina} w {self.object.miejsce}"
        )

        messages.success(request, "Msza została usunięta.")
        return super().delete(request, *args, **kwargs)


class MszaListaDrukView(MszaListaView):
    template_name = "msze/druki/msza_lista_druk.html"
    paginate_by = None

    def get_queryset(self):
        # Pobieramy queryset z logiką filtrowania z klasy nadrzędnej (MszaListaView)
        qs = super().get_queryset()
        # WAŻNE: Dodajemy prefetch_related("intencje"), 
        # aby pobrać treści intencji w jednym zapytaniu SQL (optymalizacja)
        return qs.prefetch_related("intencje")

class MszaListaPDFView(MszaListaView):
    """
    Generuje PDF z listy mszy, zachowując aktywne filtry (data, status).
    Dziedziczy po MszaListaView, więc korzysta z tego samego get_queryset.
    """
    def render_to_response(self, context, **response_kwargs):
        # Dodajemy bieżącą datę do stopki
        context['today'] = timezone.now()
        
        # Budujemy nazwę pliku, np. Wykaz_Mszy_2023-11-01.pdf
        filename = f"Wykaz_Mszy_{timezone.localdate()}.pdf"
        
        return render_to_pdf('msze/druki/msza_lista_pdf.html', context, filename)




class IntencjaNowaView(RolaWymaganaMixin, FormView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
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
            opis=f"Dodano intencję do mszy {self.msza.data} {self.msza.godzina}: {intencja.tresc[:80]}"
        )

        messages.success(self.request, "Dodano intencję do tej mszy.")
        return redirect(self.msza.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["msza"] = self.msza
        return ctx


class IntencjaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]
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
            opis=f"Zmieniono intencję dla mszy {self.object.msza.data} {self.object.msza.godzina}"
        )

        messages.success(self.request, "Zapisano zmiany intencji.")
        return response

    def get_success_url(self):
        return self.object.msza.get_absolute_url()


class IntencjaUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = IntencjaMszy
    template_name = "msze/intencja_usun.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        zapisz_log(
            request,
            "USUNIECIE_INTENCJI",
            self.object,
            opis=f"Usunięto intencję dla mszy {self.object.msza.data} {self.object.msza.godzina}"
        )

        messages.success(request, "Intencja została usunięta.")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.msza.get_absolute_url()



class KalendarzMszyView(LoginRequiredMixin, TemplateView):
    template_name = "msze/kalendarz.html"


def kalendarz_mszy_dane(request):
    """
    Zwraca listę wydarzeń dla FullCalendar z uwzględnieniem kolorów typów mszy.
    """
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")

    def parse_iso(dt_str):
        if not dt_str:
            return None
        try:
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
            data__lte=end_dt.date()
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
            # Jeśli to specjalny typ (np. Ślub), pokaż go w tytule zamiast "wolna"     
                tytul = f"{msza.get_typ_display()} - wolna"
            
        # 2. Kolor (Logika Hybrydowa)
        # Dla mszy powszedniej: Pomarańczowy (zajęta) lub Zielony (wolna - z Twojej metody)
        if msza.typ == 'POWSZEDNIA' and has_intencje:
            kolor = "#fd7e14" # pomarańczowy (Zajęta)
        else:
            # Dla wszystkich innych typów (Ślub, Pogrzeb, lub Wolna Powszednia)
            # bierzemy Twój piękny kolor z modelu
            kolor = msza.get_kolor_kalendarza()

        events.append({
            "title": tytul,
            "start": dt.isoformat(),
            "url": msza.get_absolute_url(),
            "color": kolor,
            "borderColor": "#000" if not has_intencje and msza.typ != 'POWSZEDNIA' else kolor,
            
            # DODAJ TO POLE:
            "extendedProps": {
                "isBusy": has_intencje  # True jeśli są intencje, False jeśli nie
            }
        })

    return JsonResponse(events, safe=False)