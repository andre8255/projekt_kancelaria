# msze/models.py
from django.db import models
from django.urls import reverse
from slowniki.models import Duchowny

# === NOWY KOD: Słownik typów mszy ===
class TypMszy(models.TextChoices):
    POWSZEDNIA = "POWSZEDNIA", "Powszednia"
    NIEDZIELNA = "NIEDZIELNA", "Niedzielna / Uroczystość"
    SLUBNA = "SLUBNA", "Ślubna"
    POGRZEBOWA = "POGRZEBOWA", "Pogrzebowa"
    ODPUSTOWA = "ODPUSTOWA", "Odpustowa"
    # Dodatkowe profesjonalne typy:
    GREGORIANSKA = "GREGORIANSKA", "Gregoriańska"
    ZBIOROWA = "ZBIOROWA", "Zbiorowa (wiele intencji)"
    JUBILEUSZOWA = "JUBILEUSZOWA", "Jubileuszowa (rocznice)"
    RORATNIA = "RORATNIA", "Roratnia"

class Msza(models.Model):
    data = models.DateField("Data mszy")
    godzina = models.TimeField("Godzina mszy")
    
    # === NOWE POLE ===
    typ = models.CharField(
        "Rodzaj mszy",
        max_length=20,
        choices=TypMszy.choices,
        default=TypMszy.POWSZEDNIA
    )

    miejsce = models.CharField(
        "Miejsce",
        max_length=120,
        help_text="Np. Kościół parafialny / Kaplica / Kościół filialny"
    )

    # ... reszta pól bez zmian (celebrans, celebrans_opis, uwagi) ...
    celebrans = models.ForeignKey(
        Duchowny,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Celebrans (z listy)",
        related_name="msze_odprawiane"
    )

    celebrans_opis = models.CharField(
        "Celebrans (opis ręczny)",
        max_length=120,
        blank=True,
        help_text="Wypełnij tylko jeśli celebransa nie ma na liście powyżej."
    )

    uwagi = models.TextField(
        "Uwagi (wewnętrzne)",
        blank=True,
        help_text="Np. zmiana celebransa, uwagi organizacyjne"
    )

    class Meta:
        verbose_name = "Msza"
        verbose_name_plural = "Msze"
        ordering = ["data", "godzina", "miejsce"]
        indexes = [
            models.Index(fields=["data"]),
        ]

    def __str__(self):
        # Dodajemy typ do wyświetlania
        return f"{self.data} {self.godzina} - {self.get_typ_display()}"

    # ... reszta metod (get_absolute_url, czy_zajeta) bez zmian ...
    def get_absolute_url(self):
        return reverse("msza_szczegoly", args=[self.pk])

    def czy_zajeta(self):
        return self.intencje.exists()

    def ile_intencji(self):
        return self.intencje.count()
    
    # === BONUS: Kolor dla kalendarza ===
    def get_kolor_kalendarza(self):
        """Zwraca kolor dla FullCalendar w zależności od typu"""
        kolory = {
            TypMszy.SLUBNA: "#FFD700",      # Złoty
            TypMszy.POGRZEBOWA: "#000000",  # Czarny/Ciemny
            TypMszy.NIEDZIELNA: "#dc3545",  # Czerwony
            TypMszy.GREGORIANSKA: "#6f42c1",# Fioletowy
            TypMszy.ZBIOROWA: "#0d6efd",    # Niebieski
        }
        return kolory.get(self.typ, "#198754") # Domyślny zielony (Powszednia)

# ... model IntencjaMszy bez zmian ...
class IntencjaMszy(models.Model):
    msza = models.ForeignKey(
        Msza,
        on_delete=models.CASCADE,
        related_name="intencje",
        verbose_name="Msza"
    )
    tresc = models.TextField(
        "Treść intencji",
        help_text='Np. "+ Jan Kowalski od żony i dzieci"'
    )
    zamawiajacy = models.CharField(
        "Zamawiający / od kogo",
        max_length=200,
        blank=True,
        help_text="Np. Rodzina Kowalskich"
    )
    ofiara = models.CharField(
        "Ofiara",
        max_length=120,
        blank=True,
        help_text="Kwota / dar (tylko do użytku kancelarii)"
    )
    uwagi = models.TextField(
        "Uwagi wewnętrzne",
        blank=True,
        help_text="Np. 'zarezerwowano telefonicznie'"
    )

    class Meta:
        verbose_name = "Intencja mszalna"
        verbose_name_plural = "Intencje mszalne"
        ordering = ["msza", "pk"]

    def __str__(self):
        return f"Intencja na {self.msza.data} {self.msza.godzina}: {self.tresc[:50]}..."