import os
import time
import threading
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings

class KontaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "konta"

    def ready(self):
        # Ten kod uruchamia się przy starcie aplikacji.
        # Uruchamiamy go tylko w głównym procesie (RUN_MAIN='true'),
        # żeby uniknąć podwójnego odpalania przez autoreloadera Django.
        if os.environ.get('RUN_MAIN') == 'true':
            
            # 1. WYMUSZENIE LOGOWANIA: Usuń stare sesje
            self.wyczysc_sesje()
            
            # 2. BACKUP: Uruchom wątek w tle
            self.uruchom_watek_backupu()

    def wyczysc_sesje(self):
        """Usuwa wszystkie aktywne sesje, wymuszając logowanie."""
        try:
            from django.contrib.sessions.models import Session
            count = Session.objects.all().delete()[0]
            print(f"[SECURITY] Wyczyszczono {count} starych sesji. Wymagane ponowne logowanie.")
        except Exception as e:
            print(f"[SECURITY ERROR] Nie udało się wyczyścić sesji: {e}")

    def uruchom_watek_backupu(self):
        """Uruchamia niezależny wątek sprawdzający harmonogram backupu."""
        t = threading.Thread(target=petla_sprawdzajaca_backup, daemon=True)
        t.start()
        print("[SCHEDULER] Wątek kopii zapasowych uruchomiony (tryb threading).")

# --- FUNKCJA WĄTKU TŁA ---
def petla_sprawdzajaca_backup():
    """Sprawdza co minutę, czy wykonać backup."""
    # Import wewnątrz funkcji, aby uniknąć błędu 'Apps not loaded'
    from .tasks import wykonaj_automatyczny_backup
    
    while True:
        time.sleep(300)  # Czekaj 60 sekund
        try:
            wykonaj_automatyczny_backup()
        except Exception as e:
            print(f"[SCHEDULER ERROR] Błąd w pętli backupu: {e}")
