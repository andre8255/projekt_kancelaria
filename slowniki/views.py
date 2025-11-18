# slowniki/views.py

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

# Importy ról
from konta.mixins import RolaWymaganaMixin
from konta.models import Rola

from .models import Parafia, Duchowny, Wyznanie
# Import formularzy (to przywróci wygląd!)
from .forms import ParafiaForm, DuchownyForm, WyznanieForm

# =============================================================================
# === PARAFIA
# =============================================================================

class ParafiaListaView(LoginRequiredMixin, ListView):
    model = Parafia
    template_name = "slowniki/parafia_lista.html"
    context_object_name = "parafie"
    ordering = ["miejscowosc", "nazwa"]

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            # Wyszukiwanie po nazwie i miejscowości
            from django.db.models import Q
            for s in q.split():
                qs = qs.filter(
                    Q(nazwa__icontains=s) |
                    Q(miejscowosc__icontains=s) |
                    Q(diecezja__icontains=s)
                )
        return qs
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtr_q"] = self.request.GET.get("q", "")
        return ctx


class ParafiaSzczegolyView(LoginRequiredMixin, DetailView):
    model = Parafia
    template_name = "slowniki/parafia_szczegoly.html"
    context_object_name = "parafia"


class ParafiaNowaView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN]
    model = Parafia
    form_class = ParafiaForm  # <--- PRZYWRÓCONE
    template_name = "slowniki/parafia_formularz.html"
    success_url = reverse_lazy("slownik_parafia_lista")

    def form_valid(self, form):
        messages.success(self.request, "Parafia została dodana.")
        return super().form_valid(form)


class ParafiaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN]
    model = Parafia
    form_class = ParafiaForm  # <--- PRZYWRÓCONE
    template_name = "slowniki/parafia_formularz.html"
    success_url = reverse_lazy("slownik_parafia_lista")

    def form_valid(self, form):
        messages.success(self.request, "Zmiany zapisano.")
        return super().form_valid(form)


class ParafiaUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN]
    model = Parafia
    template_name = "slowniki/parafia_usun.html"
    success_url = reverse_lazy("slownik_parafia_lista")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                f"Nie można usunąć parafii '{self.object}', "
                f"ponieważ jest ona używana w aktach sakramentów."
            )
            return redirect(self.object.get_absolute_url())
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Parafia została usunięta.")
        return super().delete(request, *args, **kwargs)

# =============================================================================
# === DUCHOWNY
# =============================================================================

class DuchownyListaView(LoginRequiredMixin, ListView):
    model = Duchowny
    template_name = "slowniki/duchowny_lista.html"
    context_object_name = "duchowni"
    ordering = ["imie_nazwisko"]
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            from django.db.models import Q
            for s in q.split():
                qs = qs.filter(Q(imie_nazwisko__icontains=s))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtr_q"] = self.request.GET.get("q", "")
        return ctx


class DuchownySzczegolyView(LoginRequiredMixin, DetailView):
    model = Duchowny
    template_name = "slowniki/duchowny_szczegoly.html"
    context_object_name = "duchowny"


class DuchownyNowyView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN]
    model = Duchowny
    form_class = DuchownyForm  # <--- PRZYWRÓCONE
    template_name = "slowniki/duchowny_formularz.html"
    success_url = reverse_lazy("slownik_duchowny_lista")

    def form_valid(self, form):
        messages.success(self.request, "Duchowny został dodany.")
        return super().form_valid(form)


class DuchownyEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN]
    model = Duchowny
    form_class = DuchownyForm  # <--- PRZYWRÓCONE
    template_name = "slowniki/duchowny_formularz.html"
    success_url = reverse_lazy("slownik_duchowny_lista")

    def form_valid(self, form):
        messages.success(self.request, "Zmiany zapisano.")
        return super().form_valid(form)


class DuchownyUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN]
    model = Duchowny
    template_name = "slowniki/duchowny_usun.html"
    success_url = reverse_lazy("slownik_duchowny_lista")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                f"Nie można usunąć duchownego '{self.object}', "
                f"ponieważ jest on używany w aktach sakramentów."
            )
            return redirect(self.object.get_absolute_url())

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Duchowny został usunięty.")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# === WYZNANIE
# =============================================================================

class WyznanieListaView(LoginRequiredMixin, ListView):
    model = Wyznanie
    template_name = "slowniki/wyznanie_lista.html"
    context_object_name = "wyznania"
    ordering = ["nazwa"]


class WyznanieNoweView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN]
    model = Wyznanie
    form_class = WyznanieForm  # <--- PRZYWRÓCONE
    template_name = "slowniki/wyznanie_formularz.html"
    success_url = reverse_lazy("slownik_wyznanie_lista")

    def form_valid(self, form):
        messages.success(self.request, "Wyznanie zostało dodane.")
        return super().form_valid(form)


class WyznanieEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN]
    model = Wyznanie
    form_class = WyznanieForm  # <--- PRZYWRÓCONE
    template_name = "slowniki/wyznanie_formularz.html"
    success_url = reverse_lazy("slownik_wyznanie_lista")

    def form_valid(self, form):
        messages.success(self.request, "Zmiany zapisano.")
        return super().form_valid(form)


class WyznanieUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN]
    model = Wyznanie
    template_name = "slowniki/potwierdz_usuniecie.html"
    success_url = reverse_lazy("slownik_wyznanie_lista")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                f"Nie można usunąć wyznania '{self.object}', "
                f"ponieważ jest ono używane w profilach osób."
            )
            return redirect(reverse_lazy("slownik_wyznanie_lista"))

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Wyznanie zostało usunięte.")
        return super().delete(request, *args, **kwargs)