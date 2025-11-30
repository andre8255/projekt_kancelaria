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
    
class LogAkcji(models.Model):
    uzytkownik = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logi",
        verbose_name="Użytkownik"
    )
    kiedy = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data i czas"
    )
    akcja = models.CharField(
        max_length=50,
        verbose_name="Akcja"
    )
    model = models.CharField(
        max_length=100,
        verbose_name="Model"
    )
    obiekt_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ID obiektu"
    )
    opis = models.TextField(
        blank=True,
        verbose_name="Opis"
    )

    class Meta:
        ordering = ["-kiedy"]
        verbose_name = "Log akcji"
        verbose_name_plural = "Logi akcji"

    def __str__(self):
        return f"[{self.kiedy}] {self.akcja} ({self.model}#{self.obiekt_id})"

