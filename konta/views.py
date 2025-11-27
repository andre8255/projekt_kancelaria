from django.views import View
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.messages import get_messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
import os
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required


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
        return redirect("logowanie")
    
# Używamy staff_member_required, aby tylko obsługa (admini) mogła pobrać bazę
@staff_member_required
def pobierz_backup(request):
    # 1. Ścieżka do pliku bazy danych (pobierana z settings.py)
    db_path = settings.DATABASES['default']['NAME']
    
    # 2. Sprawdzenie czy plik istnieje
    if not os.path.exists(db_path):
        return HttpResponse("Błąd: Nie znaleziono pliku bazy danych.", status=404)

    # 3. Otwarcie pliku w trybie binarnym (rb - read binary)
    with open(db_path, 'rb') as db_file:
        response = HttpResponse(db_file.read(), content_type='application/x-sqlite3')
        
        # 4. Wygenerowanie nazwy pliku z datą, np. parafia_backup_2023-10-27.sqlite3
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"parafia_backup_{timestamp}.sqlite3"
        
        # 5. Nagłówek informujący przeglądarkę, że to plik do pobrania
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response