
#sakramenty/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.db import models
from django import forms
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
)
from django.http import HttpResponseRedirect
from osoby.models import Osoba
from .models import Chrzest,PierwszaKomunia,Bierzmowanie,Malzenstwo,NamaszczenieChorych,Zgon
from .forms import ChrzestForm,PierwszaKomuniaForm,BierzmowanieForm,MalzenstwoForm,NamaszczenieChorychForm,ZgonForm
from django.views.generic import DeleteView
from django.contrib import messages

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

from osoby.models import Osoba
from .models import Bierzmowanie
from .forms import BierzmowanieForm


class ChrzestListaView(LoginRequiredMixin, ListView):
    model = Chrzest
    template_name = "sakramenty/chrzest_lista.html"
    context_object_name = "chrzty"
    paginate_by = 50
    ordering = ["-rok", "akt_nr"]

    def get_queryset(self):
        qs = (
            Chrzest.objects.select_related("ochrzczony")
            .order_by("-rok", "akt_nr")
        )

        # filtrowanie po roku i wyszukiwanie
        szukaj = (self.request.GET.get("q") or "").strip()
        rok = (self.request.GET.get("rok") or "").strip()

        if rok:
            qs = qs.filter(rok=rok)

        if szukaj:
            # szukaj po nazwisku, imieniu albo nr aktu
            qs = qs.filter(
                ochrzczony__nazwisko__icontains=szukaj
            ) | qs.filter(
                ochrzczony__imie_pierwsze__icontains=szukaj
            ) | qs.filter(
                akt_nr__icontains=szukaj
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


class ChrzestNowyView(LoginRequiredMixin, CreateView):
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
        o = self.osoba

        # ochrzczony – przekaż INSTANCJĘ (nie tylko pk)
        initial["ochrzczony"] = o

        # pełna data urodzenia (jeśli jest)
        if getattr(o, "data_urodzenia", None):
            initial["data_urodzenia"] = o.data_urodzenia

        # ====== NOWE: pełne imię + nazwisko rodziców ======
        def full(first, last):
            return " ".join(x for x in [first or "", last or ""] if x).strip()

        # Ojciec -> pole tekstowe Chrzest.ojciec
        ojciec_txt = full(getattr(o, "imie_ojca", ""), getattr(o, "nazwisko_ojca", ""))
        if ojciec_txt:
            initial["ojciec"] = ojciec_txt

        # Matka -> pole tekstowe Chrzest.matka
        matka_txt = full(getattr(o, "imie_matki", ""), getattr(o, "nazwisko_matki", ""))
        if matka_txt:
            initial["matka"] = matka_txt

        # Nazwisko rodowe matki — preferuj nowe pole z Osoba,
        # a jeśli puste, użyj ogólnego 'nazwisko_rodowe' jeśli kiedyś je wpisywałeś.
        rodowe = getattr(o, "nazwisko_matki_rodowe", "") or getattr(o, "nazwisko_rodowe", "")
        if rodowe:
            initial["nazwisko_matki_rodowe"] = rodowe
        # ================================================

        return initial


    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.osoba:
            obj.ochrzczony = self.osoba                        # <— tu
        obj.save()
        messages.success(self.request, "Dodano wpis chrztu.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx

    def get_success_url(self):
        if self.object and self.object.ochrzczony_id:          # <— tu
            return reverse_lazy("osoba_szczegoly", args=[self.object.ochrzczony_id])
        return reverse_lazy("chrzest_lista")


class ChrzestEdycjaView(LoginRequiredMixin, UpdateView):
    model = Chrzest
    form_class = ChrzestForm
    template_name = "sakramenty/chrzest_formularz.html"
    success_url = reverse_lazy("chrzest_lista")


class ChrzestNowyDlaOsobyView(LoginRequiredMixin, CreateView):
    model = Chrzest
    form_class = ChrzestForm
    template_name = "sakramenty/chrzest_formularz.html"

    def dispatch(self, request, *args, **kwargs):
        self.osoba = get_object_or_404(Osoba, pk=kwargs["osoba_pk"])
        if Chrzest.objects.filter(ochrzczony=self.osoba).exists():
            messages.warning(request, "Ta osoba ma już wpis chrztu.")
            return redirect(self.osoba.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)


    def get_initial(self):
        initial = super().get_initial()
        o = self.osoba

        initial["ochrzczony"] = o  # ważne: instancja, nie tylko pk

        if getattr(o, "data_urodzenia", None):
            initial["data_urodzenia"] = o.data_urodzenia

        # Ojciec (tekstowe pole w modelu Chrzest)
        ojciec_txt = " ".join(x for x in [o.imie_ojca, o.nazwisko_ojca] if x).strip()
        if ojciec_txt:
            initial["ojciec"] = ojciec_txt

        # Matka (tekstowe pole w modelu Chrzest)
        matka_txt = " ".join(x for x in [o.imie_matki, o.nazwisko_matki] if x).strip()
        if matka_txt:
            initial["matka"] = matka_txt

        # Nazwisko rodowe matki (osobne pole)
        if o.nazwisko_matki_rodowe:
            initial["nazwisko_matki_rodowe"] = o.nazwisko_matki_rodowe

        return initial


    def form_valid(self, form):
        ch = form.save(commit=False)
        ch.ochrzczony = self.osoba
        ch.save()
        messages.success(self.request, "Dodano wpis chrztu.")
        return redirect(reverse("osoba_szczegoly", args=[self.osoba.pk]))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx


class ChrzestUsunView(LoginRequiredMixin, DeleteView):
    model = Chrzest
    template_name = "sakramenty/chrzest_usun.html"
    success_url = reverse_lazy("chrzest_lista")

    def delete(self, request, *args, **kwargs):
        # żeby po usunięciu była informacja w komunikatach
        messages.success(request, "Wpis chrztu został usunięty.")
        return super().delete(request, *args, **kwargs)
    
class PierwszaKomuniaNowaDlaOsobyView(LoginRequiredMixin, CreateView):
    model = PierwszaKomunia
    form_class = PierwszaKomuniaForm
    template_name = "sakramenty/komunia_formularz.html"

    def dispatch(self, request, *args, **kwargs):
        # Zapamiętujemy osobę, żebyśmy nie musieli jej wybierać z listy
        self.osoba = get_object_or_404(Osoba, pk=kwargs["osoba_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        # nie zawsze wiemy parafię – ale jeśli chcesz możesz tu
        # ustawić domyślnie parafię własną parafii,
        # a na razie zostawmy puste
    def form_valid(self, form):
        komunia = form.save(commit=False)
        komunia.osoba = self.osoba
        komunia.save()

        messages.success(self.request, "Dodano wpis o I Komunii Świętej.")
        return redirect(reverse("osoba_szczegoly", args=[self.osoba.pk]))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx

class ChrzestDrukView(LoginRequiredMixin, DetailView):
    model = Chrzest
    template_name = "sakramenty/druki/chrzest_druk.html"
    context_object_name = "chrzest"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        osoba = self.object.ochrzczony

        bierzm = (
            Bierzmowanie.objects
            .filter(osoba=osoba)
            .select_related("parafia")
            .order_by("-data_bierzmowania", "-rok")
            .first()
        )

        ctx["bierzmowanie"] = bierzm
        ctx["today"] = timezone.localdate()
        return ctx



class KomuniaSzczegolyView(LoginRequiredMixin, DetailView):
    model = PierwszaKomunia
    template_name = "sakramenty/komunia_szczegoly.html"
    context_object_name = "komunia"

class KomuniaNowaView(LoginRequiredMixin, CreateView):
    model = PierwszaKomunia
    form_class = PierwszaKomuniaForm
    template_name = "sakramenty/komunia_formularz.html"

    # będziemy tu trzymać osobę, jeśli przyszliśmy z profilu
    osoba = None

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
            # blokada duplikatu – zakładamy 1 wpis I Komunii na osobę
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
        # jeśli przyszliśmy z profilu osoby, przypnij ją „na sztywno”
        if self.osoba:
            obj.osoba = self.osoba

        # druga warstwa zabezpieczenia przed duplikatem
        if PierwszaKomunia.objects.filter(osoba=obj.osoba).exists():
            form.add_error("osoba", "Dla tej osoby wpis I Komunii już istnieje.")
            return self.form_invalid(form)

        obj.save()
        messages.success(self.request, "Dodano wpis I Komunii Św.")
        return redirect(self.get_success_url())
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba           # do templatki
        return ctx
    
    def get_success_url(self):
        # jeśli znamy osobę – wróć do jej profilu; w innym wypadku do listy komunii
        if self.object and self.object.osoba_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.osoba_id])
        return reverse_lazy("komunia_lista")
    
    

class KomuniaEdycjaView(LoginRequiredMixin, UpdateView):
    model = PierwszaKomunia
    form_class = PierwszaKomuniaForm
    template_name = "sakramenty/komunia_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany I Komunii.")
        return self.object.osoba.get_absolute_url()


class KomuniaUsunView(LoginRequiredMixin, DeleteView):
    model = PierwszaKomunia
    template_name = "sakramenty/komunia_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis I Komunii został usunięty.")
        return self.object.osoba.get_absolute_url()

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
                    | Q(parafia__icontains=slowo)
                    | Q(rok__icontains=slowo)
                )
        return qs
    
#--------Bierzmowanie---------
class BierzmowanieNoweDlaOsobyView(LoginRequiredMixin, CreateView):
    model = Bierzmowanie
    form_class = BierzmowanieForm
    template_name = "sakramenty/bierzmowanie_formularz.html"

    def dispatch(self, request, *args, **kwargs):
        # osoba_pk z URL-a
        self.osoba = get_object_or_404(Osoba, pk=kwargs["osoba_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        # Możesz np. ustawić domyślną parafię bierzmowania jeśli zawsze ta sama,
        # ale na razie zostawiamy puste.
        return super().get_initial()

    def form_valid(self, form):
        bierzm = form.save(commit=False)
        bierzm.osoba = self.osoba
        bierzm.save()

        messages.success(self.request, "Dodano wpis bierzmowania.")
        return redirect(reverse("osoba_szczegoly", args=[self.osoba.pk]))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx

class BierzmowanieSzczegolyView(LoginRequiredMixin, DetailView):
    model = Bierzmowanie
    template_name = "sakramenty/bierzmowanie_szczegoly.html"
    context_object_name = "bierzmowanie"




class BierzmowanieNoweView(LoginRequiredMixin, CreateView):
    model = Bierzmowanie
    form_class = BierzmowanieForm
    template_name = "sakramenty/bierzmowanie_formularz.html"

    osoba = None  # ustawiamy, jeśli przyszliśmy z profilu osoby

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
            # blokada duplikatu (1 bierzmowanie na osobę)
            if Bierzmowanie.objects.filter(osoba=self.osoba).exists():
                messages.warning(request, "Ta osoba ma już wpis bierzmowania.")
                return redirect(self.osoba.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.osoba:
            initial["osoba"] = self.osoba
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)
        # jeśli start z profilu osoby – przypnij ją na stałe
        if self.osoba:
            obj.osoba = self.osoba

        # druga warstwa ochrony przed duplikatem
        if Bierzmowanie.objects.filter(osoba=obj.osoba).exists():
            form.add_error("osoba", "Dla tej osoby wpis bierzmowania już istnieje.")
            return self.form_invalid(form)

        obj.save()
        messages.success(self.request, "Dodano wpis bierzmowania.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba  # w templacie możesz warunkowo pokazywać nagłówek/nawigację
        return ctx

    def get_success_url(self):
        if self.object and self.object.osoba_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.osoba_id])
        return reverse_lazy("bierzmowanie_lista")


class BierzmowanieEdycjaView(LoginRequiredMixin, UpdateView):
    model = Bierzmowanie
    form_class = BierzmowanieForm
    template_name = "sakramenty/bierzmowanie_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany bierzmowania.")
        return self.object.osoba.get_absolute_url()

class BierzmowanieUsunView(LoginRequiredMixin, DeleteView):
    model = Bierzmowanie
    template_name = "sakramenty/bierzmowanie_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis bierzmowania został usunięty.")
        return self.object.osoba.get_absolute_url()

class BierzmowanieListaView(LoginRequiredMixin, ListView):
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
                    | Q(szafarz__imie_nazwisko__icontains=slowo)
                    | Q(rok__icontains=slowo)
                )
        return qs

#----------Małżenstwo-----------
class MalzenstwoNoweDlaOsobyView(LoginRequiredMixin, CreateView):
    model = Malzenstwo
    form_class = MalzenstwoForm
    template_name = "sakramenty/malzenstwo_formularz.html"

    def dispatch(self, request, *args, **kwargs):
        self.malzonek_a = get_object_or_404(Osoba, pk=kwargs["osoba_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["malzonek_a"] = self.malzonek_a.pk
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # ustaw i ukryj małżonka A
        if "malzonek_a" in form.fields:
            form.fields["malzonek_a"].initial = self.malzonek_a
            form.fields["malzonek_a"].widget = forms.HiddenInput()
        return form

    def form_valid(self, form):
        form.instance.malzonek_a = self.malzonek_a  # twarde przypisanie po stronie serwera
        messages.success(self.request, "Dodano wpis małżeństwa.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.malzonek_a.get_absolute_url()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["malzonek_a"] = self.malzonek_a
        return ctx

    
class MalzenstwoSzczegolyView(LoginRequiredMixin, DetailView):
    model = Malzenstwo
    template_name = "sakramenty/malzenstwo_szczegoly.html"
    context_object_name = "malzenstwo"



class MalzenstwoNoweView(LoginRequiredMixin, CreateView):
    model = Malzenstwo
    form_class = MalzenstwoForm
    template_name = "sakramenty/malzenstwo_formularz.html"

    def dispatch(self, request, *args, **kwargs):
        # jeśli wywołane z profilu osoby: /panel/osoby/<osoba_pk>/malzenstwo/nowe/
        self.malzonek_a = None
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
        # przekaż instancję Osoby do formularza
        kwargs["malzonek_a_obj"] = self.malzonek_a
        return kwargs
    
    def form_valid(self, form):
        # KLUCZOWE: nawet jeśli ukryte pole nie przyszło w POST,
        # ustawiamy malzonek_a na podstawie URL-a.
        if self.malzonek_a:
            form.instance.malzonek_a = self.malzonek_a
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["malzonek_a"] = self.malzonek_a  # szablon wie, żeby zablokować pole i ukryć „+ Nowa osoba”
        return ctx

    def get_success_url(self):
        # po zapisie – jeśli dodawane z profilu osoby, wracamy do tej osoby
        if self.object.malzonek_a_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.malzonek_a_id])
        return reverse_lazy("malzenstwo_lista")



class MalzenstwoEdycjaView(LoginRequiredMixin, UpdateView):
    model = Malzenstwo
    form_class = MalzenstwoForm
    template_name = "sakramenty/malzenstwo_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany małżeństwa.")
        # wracamy do profilu pierwszej osoby, to wystarczy
        return self.object.malzonek_a.get_absolute_url()


class MalzenstwoUsunView(LoginRequiredMixin, DeleteView):
    model = Malzenstwo
    template_name = "sakramenty/malzenstwo_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis małżeństwa został usunięty.")
        return self.object.malzonek_a.get_absolute_url()

class MalzenstwoListaView(LoginRequiredMixin, ListView):
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
                    | Q(swiadek_urzedowy__imie_nazwisko__icontains=slowo)

                )
        return qs




#-------Namaszczenie chorych------------
class NamaszczenieNoweDlaOsobyView(LoginRequiredMixin, CreateView):
    model = NamaszczenieChorych
    form_class = NamaszczenieChorychForm
    template_name = "sakramenty/namaszczenie_formularz.html"

    def dispatch(self, request, *args, **kwargs):
         # tryb z profilu osoby (może nie być w trybie z listy)
        self.osoba = None
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        # jeśli przychodzimy z profilu — niech formularz wie, kogo dotyczy
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
            # przypadek: z profilu – przypnij twardo osobę z URL
            obj.osoba = self.osoba
        else:
            # przypadek: z listy – weź osobę z formularza
            osoba_z_form = form.cleaned_data.get("osoba")
            if not osoba_z_form:
                form.add_error("osoba", "Wybierz osobę.")
                return self.form_invalid(form)
            obj.osoba = osoba_z_form

        obj.save()
        messages.success(self.request, "Dodano wpis posługi/namaszczenia.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        # Zawsze zwracaj HttpResponse (nie dict)
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        # po zapisie: jeśli mamy osobę – wróć do jej profilu, w innym razie do listy
        if self.osoba:
            return reverse("osoba_szczegoly", args=[self.osoba.pk])
        return reverse("namaszczenie_lista")


class NamaszczenieSzczegolyView(LoginRequiredMixin, DetailView):
    model = NamaszczenieChorych
    template_name = "sakramenty/namaszczenie_szczegoly.html"
    context_object_name = "namaszczenie" 

class NamaszczenieNoweView(LoginRequiredMixin, CreateView):
    model = NamaszczenieChorych
    form_class = NamaszczenieChorychForm
    template_name = "sakramenty/namaszczenie_formularz.html"

    #osoba = None  # ustawiamy, jeśli przyszliśmy z profilu osoby
    def dispatch(self, request, *args, **kwargs):
        self.osoba=None
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        initial = super().get_initial()
        osoba_pk = self.kwargs.get("osoba_pk")
        if osoba_pk:
            initial["osoba"] = get_object_or_404(Osoba, pk=osoba_pk)
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)

        if self.osoba is not None:
            # Weszliśmy z profilu — twardo przypnij osobę z URL
            obj.osoba = self.osoba
        else:
            # Weszliśmy z listy — weź osobę z formularza
            osoba_z_form = form.cleaned_data.get("osoba")
            if not osoba_z_form:
                form.add_error("osoba", "Wybierz osobę.")
                return self.form_invalid(form)
            obj.osoba = osoba_z_form

        obj.save()
        messages.success(self.request, "Dodano wpis posługi/namaszczenia.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        # ZWRACAJ HttpResponse, NIE dict – inaczej middleware się wywali
        return self.render_to_response(self.get_context_data(form=form))
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba  # w templacie możesz warunkowo pokazywać nagłówek/nawigację
        return ctx
    
    def get_success_url(self):
        if self.object and self.object.osoba_id:
            return reverse_lazy("osoba_szczegoly", args=[self.object.osoba.pk])
        return reverse_lazy("namaszczenie_lista")

class NamaszczenieEdycjaView(LoginRequiredMixin, UpdateView):
    model = NamaszczenieChorych
    form_class = NamaszczenieChorychForm
    template_name = "sakramenty/namaszczenie_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany posługi/namaszczenia.")
        return self.object.osoba.get_absolute_url()


class NamaszczenieUsunView(LoginRequiredMixin, DeleteView):
    model = NamaszczenieChorych
    template_name = "sakramenty/namaszczenie_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis posługi/namaszczenia został usunięty.")
        return self.object.osoba.get_absolute_url()

class NamaszczenieListaView(LoginRequiredMixin, ListView):
    model = NamaszczenieChorych
    template_name = "sakramenty/namaszczenie_lista.html"
    context_object_name = "namaszczenia"
    paginate_by = 20
    ordering = ["-rok", "osoba__nazwisko", "osoba__imie_pierwsze"]

    def get_queryset(self):
        qs = (
            NamaszczenieChorych.objects.all()
            .select_related(
                "osoba",    # FK do Osoba
                "szafarz",  # FK do Duchowny
            )
        )   
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(osoba__nazwisko__icontains=q) |
                models.Q(osoba__imie_pierwsze__icontains=q) |
                models.Q(miejsce__icontains=q) |
                models.Q(szafarz__imie_nazwisko__icontains=q)
            )
        return qs




#---------Zgon---------
class ZgonNowyDlaOsobyView(LoginRequiredMixin, CreateView):
    model = Zgon
    form_class = ZgonForm
    template_name = "sakramenty/zgon_formularz.html"

    def dispatch(self, request, *args, **kwargs):
        # Osoba, dla której wpisujemy zgon
        self.osoba = get_object_or_404(Osoba, pk=kwargs["osoba_pk"])

        # zabezpieczenie: jeśli osoba już ma zgon, nie pozwalamy dodać drugiego
        if hasattr(self.osoba, "zgon"):
            messages.error(request, "Ta osoba ma już wpis zgonu.")
            return redirect(reverse("osoba_szczegoly", args=[self.osoba.pk]))

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        zgon = form.save(commit=False)
        zgon.osoba = self.osoba
        zgon.save()

        messages.success(self.request, "Dodano wpis o zgonie.")
        return redirect(reverse("osoba_szczegoly", args=[self.osoba.pk]))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba
        return ctx
    
class ZgonSzczegolyView(LoginRequiredMixin, DetailView):
    model = Zgon
    template_name = "sakramenty/zgon_szczegoly.html"
    context_object_name = "zgon"

class ZgonNowyView(LoginRequiredMixin, CreateView):
    model = Zgon
    form_class = ZgonForm
    template_name = "sakramenty/zgon_formularz.html"

    osoba = None  # ustawiane, gdy wchodzimy z profilu osoby

    def dispatch(self, request, *args, **kwargs):
        osoba_pk = kwargs.get("osoba_pk")
        if osoba_pk:
            self.osoba = get_object_or_404(Osoba, pk=osoba_pk)
            # blokada duplikatu – jeden zgon na osobę
            if Zgon.objects.filter(osoba=self.osoba).exists():
                messages.warning(request, "Ta osoba ma już wpis zgonu.")
                return redirect(self.osoba.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.osoba:
            initial["osoba"] = self.osoba
            # podpowiedz rok na podstawie daty zgonu wpisanej w formularzu (jeśli będzie)
            # zostawiamy to do logiki formularza/clean() jeśli chcesz automatyzować
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["osoba"] = self.osoba  # przycisk „Powrót” w szablonie
        return ctx

    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.osoba:
            obj.osoba = self.osoba

        # druga warstwa zabezpieczenia przed duplikatem
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

class ZgonEdycjaView(LoginRequiredMixin, UpdateView):
    model = Zgon
    form_class = ZgonForm
    template_name = "sakramenty/zgon_formularz.html"

    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany przy zgonie.")
        return self.object.osoba.get_absolute_url()


class ZgonUsunView(LoginRequiredMixin, DeleteView):
    model = Zgon
    template_name = "sakramenty/zgon_usun.html"

    def get_success_url(self):
        messages.success(self.request, "Wpis zgonu został usunięty.")
        return self.object.osoba.get_absolute_url()
    

class ZgonListaView(LoginRequiredMixin, ListView):
    model = Zgon
    template_name = "sakramenty/zgon_lista.html"
    context_object_name = "zgony"
    paginate_by = 20
    ordering = ["-rok", "osoba__nazwisko", "osoba__imie_pierwsze"]

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("osoba",)
        )
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
    
# DRUKI – proste widoki tylko do renderu wydruku

class ChrzestDrukView(LoginRequiredMixin, DetailView):
    model = Chrzest
    template_name = "sakramenty/druki/chrzest_druk.html"
    context_object_name = "chrzest"
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        osoba = self.object.ochrzczony

        bierzm = (
            Bierzmowanie.objects
            .filter(osoba=osoba)
            .select_related("parafia")
            .order_by("-data_bierzmowania", "-rok")
            .first()
        )

        ctx["bierzmowanie"] = bierzm
        ctx["today"] = timezone.localdate()
        return ctx



class KomuniaDrukView(LoginRequiredMixin, DetailView):
    model = PierwszaKomunia
    template_name = "sakramenty/druki/komunia_druk.html"
    context_object_name = "komunia"

class BierzmowanieDrukView(LoginRequiredMixin, DetailView):
    model = Bierzmowanie
    template_name = "sakramenty/druki/bierzmowanie_druk.html"
    context_object_name = "bierzmowanie"

class MalzenstwoDrukView(LoginRequiredMixin, DetailView):
    model = Malzenstwo
    template_name = "sakramenty/druki/malzenstwo_druk.html"
    context_object_name = "malzenstwo"

class ZgonDrukView(LoginRequiredMixin, DetailView):
    model = Zgon
    template_name = "sakramenty/druki/zgon_druk.html"
    context_object_name = "zgon"