# msze/models.py
from django.db import models
from django.urls import reverse

from slowniki.models import Duchowny


# =============================================================================
#  Typ mszy (słownik wyboru)
# =============================================================================
class TypMszy(models.TextChoices):
    POWSZEDNIA = "POWSZEDNIA", "Powszednia"
    NIEDZIELNA = "NIEDZIELNA", "Niedzielna"
    SLUBNA = "SLUBNA", "Ślubna"
    POGRZEBOWA = "POGRZEBOWA", "Pogrzebowa"
    ODPUSTOWA = "ODPUSTOWA", "Odpustowa"
    SWIATECZNA = "SWIATECZNA", "Świąteczna"
    GREGORIANSKA = "GREGORIANSKA", "Gregoriańska"
    ZBIOROWA = "ZBIOROWA", "Zbiorowa (wiele intencji)"
    JUBILEUSZOWA = "JUBILEUSZOWA", "Jubileuszowa (rocznice)"
    RORATNIA = "RORATNIA", "Roratnia"


# =============================================================================
#  Msza Święta
# =============================================================================
class Msza(models.Model):
    data = models.DateField("Data mszy")
    godzina = models.TimeField("Godzina mszy")

    typ = models.CharField(
        "Rodzaj mszy",
        max_length=20,
        choices=TypMszy.choices,
        default=TypMszy.POWSZEDNIA,
    )

    miejsce = models.CharField(
        "Miejsce",
        max_length=120,
        help_text="Np. Kościół parafialny / Kaplica ",
    )

    celebrans = models.ForeignKey(
        Duchowny,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Celebrans (z listy)",
        related_name="msze_odprawiane",
    )

    celebrans_opis = models.CharField(
        "Celebrans (opis ręczny)",
        max_length=30,
        blank=True,
        help_text="Wypełnij tylko jeśli celebransa nie ma na liście powyżej.",
    )

    uwagi = models.TextField(
        "Uwagi (wewnętrzne)",
        blank=True,
        help_text="Np. zmiana celebransa, uwagi organizacyjne.",
    )

    class Meta:
        verbose_name = "Msza"
        verbose_name_plural = "Msze"
        ordering = ["data", "godzina", "miejsce"]
        indexes = [
            models.Index(fields=["data"]),
        ]

    def __str__(self) -> str:
        return f"{self.data} {self.godzina} – {self.get_typ_display()}"

    def get_absolute_url(self):
        return reverse("msza_szczegoly", args=[self.pk])

    def czy_zajeta(self) -> bool:
        """Zwraca True, jeśli msza ma przynajmniej jedną intencję."""
        return self.intencje.exists()

    def ile_intencji(self) -> int:
        """Zwraca liczbę intencji przypisanych do tej mszy."""
        return self.intencje.count()

    def get_kolor_kalendarza(self) -> str:
        """
        Zwraca kolor (HEX) używany w kalendarzu w zależności od typu mszy.
        Domyślnie zielony dla mszy powszednich.
        """
        kolory = {
            TypMszy.SLUBNA: "#FFD700",       # złoty
            TypMszy.POGRZEBOWA: "#000000",   # czarny
            TypMszy.NIEDZIELNA: "#dc3545",   # czerwony
            TypMszy.GREGORIANSKA: "#6f42c1", # fioletowy
            TypMszy.ZBIOROWA: "#0d6efd",     # niebieski
            TypMszy.SWIATECZNA: "#dc3545",   # czerwony
        }
        return kolory.get(self.typ, "#198754")  # domyślnie zielony


# =============================================================================
#  Intencja mszalna
# =============================================================================
class IntencjaMszy(models.Model):
    msza = models.ForeignKey(
        Msza,
        on_delete=models.CASCADE,
        related_name="intencje",
        verbose_name="Msza",
    )

    tresc = models.TextField(
        "Treść intencji",
        help_text='Np. "+ Jan Kowalski od żony i dzieci".',
    )

    zamawiajacy = models.CharField(
        "Zamawiający / od kogo",
        max_length=200,
        blank=True,
        help_text="Np. Rodzina Kowalskich.",
    )

    uwagi = models.TextField(
        "Uwagi wewnętrzne",
        blank=True,
        help_text="Np. 'zarezerwowano telefonicznie'.",
    )

    STATUS_NIEOPLACONA = "NIEOPLACONA"
    STATUS_OPLACONA = "OPLACONA"

    STATUS_OPLATY_CHOICES = [
        (STATUS_NIEOPLACONA, "Nieopłacona"),
        (STATUS_OPLACONA, "Opłacona"),
    ]

    status_oplaty = models.CharField(
        "Status opłaty",
        max_length=12,
        choices=STATUS_OPLATY_CHOICES,
        default=STATUS_NIEOPLACONA,
    )

    class Meta:
        verbose_name = "Intencja mszalna"
        verbose_name_plural = "Intencje mszalne"
        ordering = ["msza", "pk"]

    def __str__(self) -> str:
        skrot = (self.tresc[:50] + "…") if len(self.tresc) > 50 else self.tresc
        return f"Intencja na {self.msza.data} {self.msza.godzina}: {skrot}"
