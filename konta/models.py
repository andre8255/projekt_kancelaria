from django.db import models
from django.contrib.auth.models import User

class Rola(models.TextChoices):
    ADMIN = "ADMIN", "Administrator"
    KSIAZD = "KSIAZD", "Ksiądz"
    SEKRETARIAT = "SEKRET", "Sekretariat"

class Profil(models.Model):
    uzytkownik = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profil")
    rola = models.CharField(max_length=20, choices=Rola.choices, default=Rola.SEKRETARIAT)

    def __str__(self):
        return f"{self.uzytkownik.username} ({self.get_rola_display()})"
