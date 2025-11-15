from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView,DetailView
)

from .models import Parafia, Duchowny, Wyznanie
from django import forms
from django.db.models import Q

# --- wspólny mixin do bootstrapowych pól ---
class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if widget.__class__.__name__ in ["CheckboxInput", "RadioSelect", "CheckboxSelectMultiple"]:
                widget.attrs.setdefault("class", "form-check-input")
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()
            if not widget.attrs.get("placeholder") and field.label:
                widget.attrs["placeholder"] = field.label


# ---------- PARAFIA ----------

class ParafiaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Parafia
        fields = [
            "nazwa",
            "miejscowosc",
            "diecezja",

            "ulica",
            "nr_domu",
            "nr_mieszkania",
            "kod_pocztowy",
            "poczta",

            "telefon",
            "email",

            "uwagi",
        ]
        widgets = {
            "uwagi": forms.Textarea(attrs={"rows":3}),
        }


class ParafiaListaView(LoginRequiredMixin, ListView):
    model = Parafia
    template_name = "slowniki/parafia_lista.html"
    context_object_name = "parafie"
    paginate_by = 50
    ordering = ["nazwa"]

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            # pozwala wyszukiwać po nazwie i miejscowości (po słowach)
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



class ParafiaNowaView(LoginRequiredMixin, CreateView):
    model = Parafia
    form_class = ParafiaForm
    template_name = "slowniki/parafia_formularz.html"
    success_url = reverse_lazy("slownik_parafia_lista")

    def form_valid(self, form):
        messages.success(self.request, "Parafia została dodana.")
        return super().form_valid(form)


class ParafiaEdycjaView(LoginRequiredMixin, UpdateView):
    model = Parafia
    form_class = ParafiaForm
    template_name = "slowniki/parafia_formularz.html"
    success_url = reverse_lazy("slownik_parafia_lista")

    def form_valid(self, form):
        messages.success(self.request, "Zmiany zapisano.")
        return super().form_valid(form)


class ParafiaUsunView(LoginRequiredMixin, DeleteView):
    model = Parafia
    template_name = "slowniki/parafia_usun.html"
    success_url = reverse_lazy("slownik_parafia_lista")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Parafia została usunięta.")
        return super().delete(request, *args, **kwargs)
    
class ParafiaSzczegolyView(LoginRequiredMixin, DetailView):
    model = Parafia
    template_name = "slowniki/parafia_szczegoly.html"
    context_object_name = "parafia"
# ---------- DUCHOWNY ----------

class DuchownyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Duchowny
        fields = ["tytul", "imie_nazwisko", "parafia", "aktywny", "uwagi"]
        widgets = {
            "uwagi": forms.Textarea(attrs={"rows":3}),
        }


class DuchownyListaView(LoginRequiredMixin, ListView):
    model = Duchowny
    template_name = "slowniki/duchowny_lista.html"
    context_object_name = "duchowni"
    paginate_by = 50
    ordering = ["imie_nazwisko"]

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            # pozwala wyszukiwać nazwisku i parafii (po słowach)
            for s in q.split():
                qs = qs.filter(
                    Q(imie_nazwisko__icontains=s)
                  
                )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtr_q"] = self.request.GET.get("q", "")
        return ctx

class DuchownyNowyView(LoginRequiredMixin, CreateView):
    model = Duchowny
    form_class = DuchownyForm
    template_name = "slowniki/duchowny_formularz.html"
    success_url = reverse_lazy("slownik_duchowny_lista")

    def form_valid(self, form):
        messages.success(self.request, "Duchowny został dodany.")
        return super().form_valid(form)


class DuchownyEdycjaView(LoginRequiredMixin, UpdateView):
    model = Duchowny
    form_class = DuchownyForm
    template_name = "slowniki/duchowny_formularz.html"
    success_url = reverse_lazy("slownik_duchowny_lista")

    def form_valid(self, form):
        messages.success(self.request, "Zmiany zapisano.")
        return super().form_valid(form)


class DuchownyUsunView(LoginRequiredMixin, DeleteView):
    model = Duchowny
    template_name = "slowniki/duchowny_usun.html"
    success_url = reverse_lazy("slownik_duchowny_lista")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Duchowny został usunięty.")
        return super().delete(request, *args, **kwargs)

class DuchownySzczegolyView(LoginRequiredMixin, DetailView):
    model = Duchowny
    template_name = "slowniki/duchowny_szczegoly.html"
    context_object_name = "duchowny"


    
# ---------- WYZNANIE ----------

class WyznanieForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Wyznanie
        fields = ["nazwa"]


class WyznanieListaView(LoginRequiredMixin, ListView):
    model = Wyznanie
    template_name = "slowniki/wyznanie_lista.html"
    context_object_name = "wyznania"
    ordering = ["nazwa"]


class WyznanieNoweView(LoginRequiredMixin, CreateView):
    model = Wyznanie
    form_class = WyznanieForm
    template_name = "slowniki/wyznanie_formularz.html"
    success_url = reverse_lazy("slownik_wyznanie_lista")

    def form_valid(self, form):
        messages.success(self.request, "Wyznanie zostało dodane.")
        return super().form_valid(form)


class WyznanieEdycjaView(LoginRequiredMixin, UpdateView):
    model = Wyznanie
    form_class = WyznanieForm
    template_name = "slowniki/wyznanie_formularz.html"
    success_url = reverse_lazy("slownik_wyznanie_lista")

    def form_valid(self, form):
        messages.success(self.request, "Zmiany zapisano.")
        return super().form_valid(form)


class WyznanieUsunView(LoginRequiredMixin, DeleteView):
    model = Wyznanie
    template_name = "slowniki/potwierdz_usuniecie.html"
    success_url = reverse_lazy("slownik_wyznanie_lista")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Wyznanie zostało usunięte.")
        return super().delete(request, *args, **kwargs)
