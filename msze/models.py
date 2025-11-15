from django.db import models
from django.urls import reverse

class Msza(models.Model):
    data = models.DateField("Data mszy")
    godzina = models.TimeField("Godzina mszy")

    miejsce = models.CharField(
        "Miejsce",
        max_length=120,
        help_text="Np. Kościół parafialny / Kaplica / Kościół filialny"
    )

    celebrans = models.CharField(
        "Celebrans",
        max_length=120,
        blank=True,
        help_text="Kto odprawia (opcjonalnie)"
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
        return f"{self.data} {self.godzina} ({self.miejsce})"

    def get_absolute_url(self):
        return reverse("msza_szczegoly", args=[self.pk])

    def czy_zajeta(self):
        # jeśli jest przynajmniej jedna intencja → zajęta
        return self.intencje.exists()

    def ile_intencji(self):
        return self.intencje.count()


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
        # krótki podgląd
        return f"Intencja na {self.msza.data} {self.msza.godzina}: {self.tresc[:50]}..."
