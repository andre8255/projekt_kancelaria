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

# =============================================================================
# === PARAFIA
# =============================================================================

class ParafiaListaView(LoginRequiredMixin, ListView):
    model = Parafia
    template_name = "slowniki/parafia_lista.html"
    context_object_name = "parafie"
    ordering = ["miejscowosc", "nazwa"]


class ParafiaSzczegolyView(LoginRequiredMixin, DetailView):
    model = Parafia
    template_name = "slowniki/parafia_szczegoly.html"
    context_object_name = "parafia"


class ParafiaNowaView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN] # <-- TYLKO ADMIN
    model = Parafia
    fields = "__all__"
    template_name = "slowniki/parafia_formularz.html"
    success_url = reverse_lazy("parafia_lista")


class ParafiaEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN] # <-- TYLKO ADMIN
    model = Parafia
    fields = "__all__"
    template_name = "slowniki/parafia_formularz.html"
    success_url = reverse_lazy("parafia_lista")


class ParafiaUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN] # <-- TYLKO ADMIN
    model = Parafia
    template_name = "slowniki/parafia_usun.html"
    success_url = reverse_lazy("parafia_lista")

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

# =============================================================================
# === DUCHOWNY
# =============================================================================

class DuchownyListaView(LoginRequiredMixin, ListView):
    model = Duchowny
    template_name = "slowniki/duchowny_lista.html"
    context_object_name = "duchowni"
    ordering = ["nazwisko", "imie"]


class DuchownySzczegolyView(LoginRequiredMixin, DetailView):
    model = Duchowny
    template_name = "slowniki/duchowny_szczegoly.html"
    context_object_name = "duchowny"


class DuchownyNowyView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN] # <-- TYLKO ADMIN
    model = Duchowny
    fields = "__all__"
    template_name = "slowniki/duchowny_formularz.html"
    success_url = reverse_lazy("duchowny_lista")


class DuchownyEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN] # <-- TYLKO ADMIN
    model = Duchowny
    fields = "__all__"
    template_name = "slowniki/duchowny_formularz.html"
    success_url = reverse_lazy("duchowny_lista")


class DuchownyUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN] # <-- TYLKO ADMIN
    model = Duchowny
    template_name = "slowniki/duchowny_usun.html"
    success_url = reverse_lazy("duchowny_lista")

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

# =============================================================================
# === WYZNANIE
# =============================================================================

class WyznanieListaView(LoginRequiredMixin, ListView):
    model = Wyznanie
    template_name = "slowniki/wyznanie_lista.html"
    context_object_name = "wyznania"
    ordering = ["nazwa"]


class WyznanieNoweView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN] # <-- TYLKO ADMIN
    model = Wyznanie
    fields = "__all__"
    template_name = "slowniki/wyznanie_formularz.html"
    success_url = reverse_lazy("wyznanie_lista")


class WyznanieEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN] # <-- TYLKO ADMIN
    model = Wyznanie
    fields = "__all__"
    template_name = "slowniki/wyznanie_formularz.html"
    success_url = reverse_lazy("wyznanie_lista")


class WyznanieUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN] # <-- TYLKO ADMIN
    model = Wyznanie
    template_name = "slowniki/potwierdz_usuniecie.html" # Używamy generycznego szablonu
    success_url = reverse_lazy("wyznanie_lista")

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
            return redirect(reverse_lazy("wyznanie_lista"))