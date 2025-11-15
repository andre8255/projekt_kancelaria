# konta/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class KontaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "konta"

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    # Importy wewnątrz funkcji, żeby uniknąć cykli importów
    from django.contrib.auth.models import Group
    for name in ["Proboszcz", "Wikariusz", "Sekretariat"]:
        Group.objects.get_or_create(name=name)
