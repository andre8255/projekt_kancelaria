# cmentarz/models.py

from datetime import timedelta

from django.db import models
from django.urls import reverse
from django.utils import timezone

from osoby.models import Osoba


class Sektor(models.Model):
    # Jednostka organizacyjna cmentarza (np. sektor/kwatera), wykorzystywana do porządkowania grobów.
    nazwa = models.CharField("Sektor / Kwatera", max_length=50)
    opis = models.TextField(blank=True)

    class Meta:
        verbose_name = "Sektor cmentarza"
        verbose_name_plural = "Sektory cmentarza"

    def __str__(self):
        return self.nazwa


class Grob(models.Model):
    # Słownik typów grobów używany w formularzach oraz filtrowaniu danych.
    TYPY = [
        ("ZIEMNY_1", "Ziemny pojedynczy"),
        ("ZIEMNY_2", "Ziemny podwójny"),
        ("MUROWANY_1", "Murowany pojedynczy"),
        ("MUROWANY_2", "Murowany rodzinny"),
        ("URNOWY", "Urnowy"),
        ("DZIECIECY", "Dziecięcy"),
    ]

    # Dane identyfikacyjne grobu (lokalizacja w obrębie cmentarza).
    sektor = models.ForeignKey(
        Sektor,
        on_delete=models.CASCADE,
        related_name="groby",
        verbose_name="Sektor",
    )
    rzad = models.CharField("Rząd", max_length=20, blank=True)
    numer = models.CharField("Numer grobu", max_length=20)
    typ = models.CharField("Typ grobu", max_length=20, choices=TYPY, default="ZIEMNY_1")

    # Osoba odpowiedzialna za grób (np. opiekun/dysponent wskazywany przy rozliczeniach).
    dysponent = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groby_dysponowane",
        verbose_name="Dysponent (Opiekun)",
    )

    # Informacje rozliczeniowe: data opłaty oraz termin ważności (prolongata).
    data_oplaty = models.DateField("Data wniesienia opłaty", default=timezone.now)
    wazny_do = models.DateField("Ważny do (Prolongata)", blank=True, null=True)

    # Dane dodatkowe (opis i materiał zdjęciowy).
    uwagi = models.TextField(blank=True)
    zdjecie = models.ImageField(
        "Zdjęcie nagrobka",
        upload_to="cmentarz/nagrobki/",
        blank=True,
        null=True,
    )

    class Meta:
        # W obrębie sektora obowiązuje unikalność oznaczenia grobu (sektor + rząd + numer).
        unique_together = ("sektor", "rzad", "numer")
        ordering = ["sektor", "numer"]
        verbose_name = "Grób"
        verbose_name_plural = "Groby"

    def __str__(self):
        # Reprezentacja przyjazna użytkownikowi (czytelna w listach i polach wyboru).
        if self.rzad:
            return f"{self.sektor} / Rząd {self.rzad} / Nr {self.numer}"
        return f"{self.sektor} / Nr {self.numer}"

    def get_absolute_url(self):
        # Adres widoku szczegółów grobu (używany m.in. przy przekierowaniach).
        return reverse("cmentarz:grob_szczegoly", args=[self.pk])

    def save(self, *args, **kwargs):
        # Automatyczne wyliczanie terminu ważności:
        # jeżeli użytkownik podał datę opłaty, ale nie podał "ważny do", system ustawia +20 lat.
        if self.data_oplaty and not self.wazny_do:
            try:
                self.wazny_do = self.data_oplaty.replace(year=self.data_oplaty.year + 20)
            except ValueError:
                # Obsługa przypadku 29 lutego, gdy rok docelowy nie jest przestępny.
                self.wazny_do = self.data_oplaty.replace(
                    year=self.data_oplaty.year + 20,
                    month=2,
                    day=28,
                )

        super().save(*args, **kwargs)

    @property
    def status_oplaty(self):
        # Status opłaty pomocny w listach i alertach (np. przeterminowane / kończące się).
        if not self.wazny_do:
            return "UNKNOWN"

        dzis = timezone.localdate()

        if self.wazny_do < dzis:
            return "EXPIRED"
        if self.wazny_do < dzis + timedelta(days=365):
            return "WARNING"
        return "OK"


class Pochowany(models.Model):
    # Powiązanie osoby z grobem wraz z datą pochówku (w grobie może być wiele osób).
    grob = models.ForeignKey(Grob, on_delete=models.CASCADE, related_name="pochowani")
    osoba = models.ForeignKey(
        Osoba,
        on_delete=models.CASCADE,
        related_name="miejsce_spoczynku",
        verbose_name="Osoba zmarła",
    )
    data_pochowania = models.DateField("Data pogrzebu", default=timezone.now)

    class Meta:
        verbose_name = "Osoba pochowana"
        verbose_name_plural = "Osoby pochowane"
        ordering = ["-data_pochowania"]

    def __str__(self):
        return f"{self.osoba} (Grób {self.grob})"
