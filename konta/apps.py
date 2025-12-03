# konta/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings

class KontaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "konta"

    def ready(self):
        # Ten kod uruchomi się przy starcie serwera
        # Sprawdzamy czy to nie jest przeładowanie deweloperskie (żeby nie odpalać podwójnie)
        import os
        if os.environ.get('RUN_MAIN', None) != 'true' and settings.DEBUG:
             return

        from . import tasks
        from apscheduler.schedulers.background import BackgroundScheduler
        
        # Tworzymy scheduler działający w tle
        scheduler = BackgroundScheduler()
        
        # Dodajemy zadanie:
        # Opcja A: Co określony czas (np. co 24 godziny)
        # scheduler.add_job(tasks.wykonaj_automatyczny_backup, 'interval', hours=24)
        
        # Opcja B: Codziennie o konkretnej godzinie (np. 22:00) - LEPSZA DLA PARAFII
       # scheduler.add_job(tasks.wykonaj_automatyczny_backup, 'cron', hour=22, minute=00)
        
        # Opcja C (do testów): Co 1 minutę - ODKOMENTUJ ŻEBY SPRAWDZIĆ CZY DZIAŁA
        #scheduler.add_job(tasks.wykonaj_automatyczny_backup, 'interval', minutes=1)

        scheduler.start()
        print("[SCHEDULER] Harmonogram kopii zapasowych uruchomiony.")



@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    # Importy wewnątrz funkcji, żeby uniknąć cykli importów
    from django.contrib.auth.models import Group
    for name in ["Proboszcz", "Wikariusz", "Sekretariat"]:
        Group.objects.get_or_create(name=name)
