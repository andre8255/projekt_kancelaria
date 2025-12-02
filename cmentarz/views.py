# cmentarz/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone

from parafia.utils_pdf import render_to_pdf
from konta.mixins import RolaWymaganaMixin
from konta.models import Rola

from .models import Grob, Sektor, Pochowany
from .forms import GrobForm, SektorForm, PochowanyForm

# --- LISTA GROBÓW ---
class GrobListaView(LoginRequiredMixin, ListView):
    model = Grob
    template_name = "cmentarz/lista.html"
    context_object_name = "groby"
    paginate_by = 20

    def get_queryset(self):
        qs = Grob.objects.select_related("sektor", "dysponent").prefetch_related("pochowani__osoba")
        
        q = self.request.GET.get("q")
        if q:
            # Szukamy po: numerze grobu, nazwisku dysponenta LUB nazwisku pochowanego
            qs = qs.filter(
                Q(rzad__icontains=q) |
                Q(numer__icontains=q) |
                Q(dysponent__nazwisko__icontains=q) |
                Q(pochowani__osoba__nazwisko__icontains=q)
            ).distinct()
            
        sektor = self.request.GET.get("sektor")
        if sektor:
            qs = qs.filter(sektor_id=sektor)
            
        return qs.order_by('sektor', 'numer')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sektory"] = Sektor.objects.all()
        return ctx

# --- SZCZEGÓŁY GROBU ---
class GrobSzczegolyView(LoginRequiredMixin, DetailView):
    model = Grob
    template_name = "cmentarz/szczegoly.html"
    context_object_name = "grob"

# --- EDYCJA / DODAWANIE ---
class GrobNowyView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Grob
    form_class = GrobForm
    template_name = "cmentarz/formularz.html"
    
    def get_success_url(self):
        return reverse_lazy("cmentarz:grob_szczegoly", args=[self.object.pk])

class GrobEdycjaView(RolaWymaganaMixin, UpdateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Grob
    form_class = GrobForm
    template_name = "cmentarz/formularz.html"
    
    def get_success_url(self):
        messages.success(self.request, "Zapisano zmiany w karcie grobu.")
        return reverse_lazy("cmentarz:grob_szczegoly", args=[self.object.pk])

class GrobUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Grob
    template_name = "cmentarz/grob_usun.html"
    success_url = reverse_lazy("cmentarz:grob_lista")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Grób został usunięty z ewidencji.")
        return super().delete(request, *args, **kwargs)

# --- DODAWANIE OSOBY ZMARŁEJ DO GROBU ---
class PochowanyNowyView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Pochowany
    form_class = PochowanyForm
    template_name = "cmentarz/pochowany_formularz.html"

    def dispatch(self, request, *args, **kwargs):
        self.grob = get_object_or_404(Grob, pk=kwargs['grob_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        pochowany = form.save(commit=False)
        pochowany.grob = self.grob
        pochowany.save()
        messages.success(self.request, "Dodano osobę do grobu.")
        return redirect(self.grob.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['grob'] = self.grob
        return ctx
    
class PochowanyUsunView(RolaWymaganaMixin, DeleteView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Pochowany
    template_name = "cmentarz/pochowany_usun.html"

    def get_success_url(self):
        grob = self.object.grob
        messages.success(self.request, "Osoba została usunięta z grobu.")
        # Wracamy do szczegółów grobu, z którego usunęliśmy osobę
        return reverse_lazy("cmentarz:grob_szczegoly", args=[grob.pk])



# --- PDF: KARTA GROBU / WEZWANIE ---
class GrobPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        grob = get_object_or_404(Grob, pk=kwargs['pk'])
        context = {
            'grob': grob,
            'today': timezone.now(),
            # 'parafia': ... (dodawane automatycznie)
        }
        filename = f"Karta_Grobu_{grob.sektor}_{grob.numer}.pdf"
        return render_to_pdf('cmentarz/druki/karta_grobu_pdf.html', context, filename)
    
# --- ZARZĄDZANIE SEKTORAMI ---
class SektorListaView(LoginRequiredMixin, ListView):
    model = Sektor
    template_name = "cmentarz/sektor_lista.html"
    context_object_name = "sektory"

class SektorNowyView(RolaWymaganaMixin, CreateView):
    dozwolone_role = [Rola.ADMIN, Rola.KSIAZD]
    model = Sektor
    form_class = SektorForm
    template_name = "cmentarz/sektor_formularz.html"
    success_url = reverse_lazy("cmentarz:sektor_lista") # Pamiętaj o namespace!

    def form_valid(self, form):
        messages.success(self.request, "Dodano nowy sektor.")
        return super().form_valid(form)