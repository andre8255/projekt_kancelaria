from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import time

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

class BackupUstawienia(models.Model):
    CZESTOTLIWOSC_NEVER = "never"
    CZESTOTLIWOSC_DAILY = "daily"
    CZESTOTLIWOSC_WEEKLY = "weekly"
    CZESTOTLIWOSC_MONTHLY = "monthly"

    CZESTOTLIWOSC_CHOICES = [
        (CZESTOTLIWOSC_NEVER, "Tylko ręcznie"),
        (CZESTOTLIWOSC_DAILY, "Codziennie"),
        (CZESTOTLIWOSC_WEEKLY, "Raz w tygodniu"),
        (CZESTOTLIWOSC_MONTHLY, "Raz w miesiącu"),
    ]

    DNI_TYGODNIA_CHOICES = [
        ("mon", "Poniedziałek"),
        ("tue", "Wtorek"),
        ("wed", "Środa"),
        ("thu", "Czwartek"),
        ("fri", "Piątek"),
        ("sat", "Sobota"),
        ("sun", "Niedziela"),
    ]

    czestotliwosc = models.CharField(
        "Częstotliwość backupu",
        max_length=20,
        choices=CZESTOTLIWOSC_CHOICES,
        default=CZESTOTLIWOSC_DAILY,
    )

    dzien_tygodnia = models.CharField(
        "Dzień tygodnia (dla backupu tygodniowego)",
        max_length=3,
        choices=DNI_TYGODNIA_CHOICES,
        default="mon",
        help_text="Używane, gdy częstotliwość ustawiona jest na 'Raz w tygodniu'."
    )

    godzina = models.TimeField(
        "Godzina uruchamiania",
        default=time(2, 0),  # 02:00
        help_text="Godzina, o której ma być wykonywany backup."
    )

    ostatni_backup = models.DateTimeField(
        "Ostatnio wykonany backup",
        null=True,
        blank=True,
        help_text="Uzupełniane automatycznie przez mechanizm backupu."
    )

    włączony = models.BooleanField(
        "Włącz automatyczne backupy",
        default=True,
    )

    class Meta:
        verbose_name = "Ustawienia backupu"
        verbose_name_plural = "Ustawienia backupu"

    def __str__(self):
        return "Ustawienia backupu"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj