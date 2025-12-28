# rodziny/models.py
from django.db import models
from django.urls import reverse

from django.utils import timezone  # (na razie niewykorzystane, ale zostawiam)
from osoby.models import Osoba
from slowniki.models import Duchowny


class Rodzina(models.Model):
    nazwa = models.CharField(
        max_length=200,
    )

    ulica = models.CharField(max_length=120, blank=True)
    nr_domu = models.CharField(max_length=30, blank=True)
    nr_mieszkania = models.CharField(max_length=30, blank=True)
    kod_pocztowy = models.CharField(max_length=15, blank=True)
    miejscowosc = models.CharField(max_length=120, blank=True)
    poczta = models.CharField(max_length=120, blank=True)

    telefon_kontaktowy = models.CharField(max_length=40, blank=True)
    email_kontaktowy = models.EmailField(blank=True)

    uwagi = models.TextField(blank=True)

    class Meta:
        verbose_name = "Rodzina / kartoteka"
        verbose_name_plural = "Rodziny / kartoteki"
        ordering = ["miejscowosc", "ulica", "nr_domu", "nr_mieszkania", "nazwa"]
        indexes = [
            models.Index(fields=["miejscowosc", "ulica", "nr_domu"]),
        ]

    def __str__(self) -> str:
        """
        Zwraca czytelną nazwę rodziny wraz z adresem,
        np. "Kowalscy (ul. Polna 12/3, Parafia Dolna)".
        """
        adres = f"{self.ulica} {self.nr_domu}".strip()

        if self.nr_mieszkania:
            adres += f"/{self.nr_mieszkania}"

        if self.miejscowosc:
            if adres:
                adres += f", {self.miejscowosc}"
            else:
                adres = self.miejscowosc

        return f"{self.nazwa} ({adres})" if adres else self.nazwa

    def get_absolute_url(self):
        return reverse("rodzina_szczegoly", args=[self.pk])


class StatusZamieszkania(models.TextChoices):
    MIESZKA = "MIESZKA", "Mieszka"
    WYPROWADZIL_SIE = "WYPROW", "Wyprowadził(a) się"
    ZMARL = "ZMARL", "Zmarł(a)"


class RolaWRodzinie(models.TextChoices):
    MAZ = "MAZ", "Mąż"
    ZONA = "ZONA", "Żona"
    DZIECKO = "DZIECKO", "Dziecko"
    INNA = "INNA", "Inna rola"


class CzlonkostwoRodziny(models.Model):
    rodzina = models.ForeignKey(
        Rodzina,
        on_delete=models.CASCADE,
        related_name="czlonkowie",
    )
    osoba = models.ForeignKey(
        Osoba,
        on_delete=models.CASCADE,
        related_name="przynaleznosci_rodzinne",
        help_text="Osoba przypisana do tej rodziny",
    )

    rola = models.CharField(
        max_length=20,
        choices=RolaWRodzinie.choices,
        default=RolaWRodzinie.INNA,
    )

    status = models.CharField(
        "Status zamieszkania",
        max_length=20,
        choices=StatusZamieszkania.choices,
        default=StatusZamieszkania.MIESZKA,
    )

    uwagi = models.TextField(blank=True)

    class Meta:
        verbose_name = "Członek rodziny"
        verbose_name_plural = "Członkowie rodziny"
        ordering = ["rola", "osoba__nazwisko", "osoba__imie_pierwsze"]
        unique_together = ("rodzina", "osoba")

    def __str__(self) -> str:
        return f"{self.osoba} jako {self.get_rola_display()} ({self.get_status_display()})"


class WizytaDuszpasterska(models.Model):
    STATUSY = [
        ("PRZYJETA", "Wizyta przyjęta"),
        ("NIEOBECNI", "Nieobecni / Zamknięte"),
        ("ODMOWA", "Odmowa przyjęcia"),
        ("INNE", "Inne"),
    ]

    rodzina = models.ForeignKey(
        Rodzina,
        on_delete=models.CASCADE,
        related_name="wizyty",
        verbose_name="Rodzina",
    )

    rok = models.IntegerField("Rok wizyty")
    data_wizyty = models.DateField("Data wizyty", null=True, blank=True)

    ksiadz = models.ForeignKey(
        Duchowny,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ksiądz odwiedzający",
    )

    status = models.CharField(
        "Status",
        max_length=20,
        choices=STATUSY,
        default="PRZYJETA",
    )

    ofiara = models.CharField(
        "Ofiara",
        max_length=100,
        blank=True,
        help_text="Opcjonalnie",
    )
    notatka = models.TextField(
        "Notatki duszpasterskie",
        blank=True,
    )

    class Meta:
        verbose_name = "Wizyta duszpasterska"
        verbose_name_plural = "Wizyty duszpasterskie"
        ordering = ["-rok", "-data_wizyty"]

    def __str__(self) -> str:
        return f"Kolęda {self.rok} – {self.rodzina}"
