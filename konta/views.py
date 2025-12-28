import os

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, UpdateView

from parafia.utils_pdf import render_to_pdf

from .forms import BackupUstawieniaForm
from .models import BackupUstawienia, LogAkcji
from .utils_backup import wykonaj_backup_bazy


class LogowanieView(LoginView):
    template_name = "konta/logowanie.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        # skonsumuj ewentualne stare wiadomości (np. „Wylogowano.”)
        list(get_messages(self.request))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("panel_start")


class WylogujView(View):
    def post(self, request):
        logout(request)
        messages.success(request, "Wylogowano.")
        return redirect("konta:logowanie")


# Używamy staff_member_required, aby tylko obsługa (admini) mogła pobrać bazę
@staff_member_required
def pobierz_backup(request):
    # 1. Ścieżka do pliku bazy danych (pobierana z settings.py)
    db_path = settings.DATABASES["default"]["NAME"]

    # 2. Sprawdzenie czy plik istnieje
    if not os.path.exists(db_path):
        return HttpResponse("Błąd: Nie znaleziono pliku bazy danych.", status=404)

    # 3. Otwarcie pliku w trybie binarnym (rb - read binary)
    with open(db_path, "rb") as db_file:
        response = HttpResponse(db_file.read(), content_type="application/x-sqlite3")

        # 4. Wygenerowanie nazwy pliku z datą, np. parafia_backup_2023-10-27.sqlite3
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"parafia_backup_{timestamp}.sqlite3"

        # 5. Nagłówek informujący przeglądarkę, że to plik do pobrania
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response


class LogAkcjiListaView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = LogAkcji
    template_name = "konta/log_akcji_lista.html"
    context_object_name = "logi"
    paginate_by = 50

    def test_func(self):
        """
        Dostęp tylko dla proboszcza (grupa 'Proboszcz') albo superusera.
        Możesz to dostosować do swojego systemu ról.
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.groups.filter(name="Proboszcz").exists()


class LogAkcjiPDFView(LogAkcjiListaView):
    """
    Generuje PDF z historii operacji – bez paginacji, wszystkie wpisy.
    """
    paginate_by = None
    template_name = "konta/log_akcji_pdf.html"

    def render_to_response(self, context, **response_kwargs):
        context["today"] = timezone.localdate()
        filename = f"Historia_operacji_{timezone.localdate()}.pdf"
        return render_to_pdf("konta/log_akcji_pdf.html", context, filename)


class BackupUstawieniaView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BackupUstawienia
    form_class = BackupUstawieniaForm
    template_name = "konta/backup_ustawienia.html"
    success_url = reverse_lazy("konta:backup_ustawienia")

    def get_object(self, queryset=None):
        return BackupUstawienia.get_solo()

    def test_func(self):
        u = self.request.user
        if not u.is_authenticated:
            return False
        return u.is_superuser  # ewentualnie rozbuduj o role

    def form_valid(self, form):
        messages.success(self.request, "Zapisano ustawienia harmonogramu backupu.")
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        # Jeśli kliknięto przycisk "Wykonaj backup teraz"
        if "backup_teraz" in request.POST:
            try:
                sciezka = wykonaj_backup_bazy(request, powod="RĘCZNY")
                nazwa = os.path.basename(sciezka)
                messages.success(request, f"Wykonano ręczną kopię bazy: {nazwa}")
            except Exception as e:
                messages.error(request, f"Nie udało się wykonać backupu: {e}")
            return redirect(self.success_url)

        # Standardowe zapisanie formularza (zmiana ustawień)
        return super().post(request, *args, **kwargs)
