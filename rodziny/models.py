# rodziny/models.py
from django.db import models
from django.urls import reverse
from osoby.models import Osoba

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

    def __str__(self):
        adres = f"{self.ulica} {self.nr_domu}"
        if self.nr_mieszkania:
            adres += f"/{self.nr_mieszkania}"
        if self.miejscowosc:
            adres += f", {self.miejscowosc}"
        return f"{self.nazwa} ({adres})"

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
        related_name="czlonkowie"
    )
    osoba = models.ForeignKey(
        Osoba,
        on_delete=models.CASCADE,
        related_name="przynaleznosci_rodzinne",
        help_text="Osoba przypisana do tej rodziny"
    )

    rola = models.CharField(
        max_length=20,
        choices=RolaWRodzinie.choices,
        default=RolaWRodzinie.INNA
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

    def __str__(self):
        return f"{self.osoba} jako {self.get_rola_display()} ({self.get_status_display()})"
