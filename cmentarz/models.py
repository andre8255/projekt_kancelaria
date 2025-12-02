# cmentarz/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from osoby.models import Osoba

class Sektor(models.Model):
    nazwa = models.CharField("Sektor / Kwatera", max_length=50)
    opis = models.TextField(blank=True)

    def __str__(self):
        return self.nazwa

    class Meta:
        verbose_name = "Sektor cmentarza"
        verbose_name_plural = "Sektory cmentarza"

class Grob(models.Model):
    TYPY = [
        ('ZIEMNY_1', 'Ziemny pojedynczy'),
        ('ZIEMNY_2', 'Ziemny podwójny'),
        ('MUROWANY_1', 'Murowany pojedynczy'),
        ('MUROWANY_2', 'Murowany rodzinny'),
        ('URNOWY', 'Urnowy'),
        ('DZIECIECY', 'Dziecięcy'),
    ]

    sektor = models.ForeignKey(Sektor, on_delete=models.CASCADE, related_name="groby", verbose_name="Sektor")
    rzad = models.CharField("Rząd", max_length=20, blank=True)
    numer = models.CharField("Numer grobu", max_length=20)
    typ = models.CharField("Typ grobu", max_length=20, choices=TYPY, default='ZIEMNY_1')
    
    # Kto zarządza grobem
    dysponent = models.ForeignKey(
        Osoba, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="groby_dysponowane", 
        verbose_name="Dysponent (Opiekun)"
    )
    
    # Finanse
    data_oplaty = models.DateField("Data wniesienia opłaty", default=timezone.now)
    wazny_do = models.DateField("Ważny do (Prolongata)", blank=True, null=True)
    
    uwagi = models.TextField(blank=True)
    zdjecie = models.ImageField("Zdjęcie nagrobka", upload_to="cmentarz/nagrobki/", blank=True, null=True)

    class Meta:
        # --- ZMIANA TUTAJ ---
        # Unikalna kombinacja: Sektor + rzad+  numer
        unique_together = ('sektor', 'rzad','numer')
        ordering = ['sektor', 'numer']
        verbose_name = "Grób"
        verbose_name_plural = "Groby"

    def __str__(self):
        # Ładniejsze wyświetlanie
        if self.rzad:
            return f"{self.sektor} / Rząd {self.rzad} / Nr {self.numer}"
        return f"{self.sektor} / Nr {self.numer}"

    def get_absolute_url(self):
        return reverse("cmentarz:grob_szczegoly", args=[self.pk])

    def save(self, *args, **kwargs):
        if self.data_oplaty and not self.wazny_do:
            try:
                self.wazny_do = self.data_oplaty.replace(year=self.data_oplaty.year + 20)
            except ValueError:
                self.wazny_do = self.data_oplaty + timedelta(days=365*20 + 5)
        super().save(*args, **kwargs)

    @property
    def status_oplaty(self):
        if not self.wazny_do: return "UNKNOWN"
        dzis = timezone.localdate()
        if self.wazny_do < dzis:
            return "EXPIRED"
        if self.wazny_do < dzis + timedelta(days=365):
            return "WARNING"
        return "OK"

class Pochowany(models.Model):
    grob = models.ForeignKey(Grob, on_delete=models.CASCADE, related_name="pochowani")
    osoba = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="miejsce_spoczynku", verbose_name="Osoba zmarła")
    data_pochowania = models.DateField("Data pogrzebu", default=timezone.now)
    
    class Meta:
        verbose_name = "Osoba pochowana"
        verbose_name_plural = "Osoby pochowane"
        ordering = ['-data_pochowania']

    def __str__(self):
        return f"{self.osoba} (Grób {self.grob})"