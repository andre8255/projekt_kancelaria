#konta/models/py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import time

class Rola(models.TextChoices):
    ADMIN = "ADMIN", "Administrator"
    KSIADZ = "KSIADZ", "Ksiądz"
    SEKRETARIAT = "SEKRET", "Sekretariat"

class Profil(models.Model):
    uzytkownik = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profil")
    rola = models.CharField(max_length=30, choices=Rola.choices, default=Rola.SEKRETARIAT)

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

class BackupUstawienia(models.Model):
    CZEST_DZIENNIE = "dziennie"
    CZEST_TYGODNIOWO = "tygodniowo"
    CZEST_MIESIECZNIE = "miesiecznie"

    CZESTOTLIWOSC_CHOICES = [
        (CZEST_DZIENNIE, "Raz dziennie"),
        (CZEST_TYGODNIOWO, "Raz w tygodniu"),
        (CZEST_MIESIECZNIE, "Raz w miesiącu"),
    ]

    # NOWE: choices dla dnia tygodnia
    DZIEN_TYGODNIA_CHOICES = [
        (0, "Poniedziałek"),
        (1, "Wtorek"),
        (2, "Środa"),
        (3, "Czwartek"),
        (4, "Piątek"),
        (5, "Sobota"),
        (6, "Niedziela"),
    ]

    wlaczony = models.BooleanField(
        default=False,
        verbose_name="Włącz automatyczne backupy",
    )

    czestotliwosc = models.CharField(
        max_length=20,
        choices=CZESTOTLIWOSC_CHOICES,
        default=CZEST_DZIENNIE,
        verbose_name="Częstotliwość",
    )

    dzien_tygodnia = models.IntegerField(
        choices=DZIEN_TYGODNIA_CHOICES,   # ← TU JEST MAGIA
        null=True,
        blank=True,
        verbose_name="Dzień tygodnia (dla backupu tygodniowego)",
    )

    godzina = models.TimeField(
        default=time(2, 0),
        verbose_name="Godzina uruchamiania",
    )

    ostatni_backup = models.DateTimeField(
        "Ostatni wykonany backup",
        null=True,
        blank=True
    )
    class Meta:
        verbose_name = "Ustawienia backupu"
        verbose_name_plural = "Ustawienia backupu"

    def __str__(self):
        return "Ustawienia backupu"

    @classmethod
    def get_solo(cls):
        """
        Zwraca jedyny rekord z ustawieniami backupu.
        Jeśli go nie ma – tworzy z domyślnymi wartościami.
        """
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj