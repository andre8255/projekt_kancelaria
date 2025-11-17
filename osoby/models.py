# osoby/models.py
from django.db import models
from django.urls import reverse

class Osoba(models.Model):
    nazwisko = models.CharField(max_length=120)
    imie_pierwsze = models.CharField("Imię", max_length=120)
    imie_drugie = models.CharField(max_length=120, blank=True)
    nazwisko_rodowe = models.CharField(max_length=120, blank=True)

    imie_ojca = models.CharField(max_length=120, blank=True)
    imie_matki = models.CharField(max_length=120, blank=True)

     # ⬇⬇⬇ NOWE POLA
    nazwisko_ojca = models.CharField("Nazwisko ojca", max_length=120, blank=True)
    nazwisko_matki = models.CharField("Nazwisko matki (aktualne)", max_length=120, blank=True)
    nazwisko_matki_rodowe = models.CharField("Nazwisko rodowe matki", max_length=120, blank=True)
    # ⬆⬆⬆

    # NOWE POLE:
    imie_bierzmowanie = models.CharField(
        "Imię z bierzmowania",
        max_length=120,
        blank=True,
        help_text="Imię przyjęte przy bierzmowaniu (jeśli dotyczy)."
    )

    data_urodzenia = models.DateField()
    miejsce_urodzenia = models.CharField(max_length=200, blank=True)

    data_zgonu = models.DateField(null=True, blank=True)

    ulica = models.CharField(max_length=120, blank=True)
    nr_domu = models.CharField(max_length=30, blank=True)
    nr_mieszkania = models.CharField(max_length=30, blank=True)
    kod_pocztowy = models.CharField(max_length=15, blank=True)
    miejscowosc = models.CharField(max_length=120, blank=True)
    poczta = models.CharField(max_length=120, blank=True)

    telefon = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)

    wyznanie = models.ForeignKey(
    "slowniki.Wyznanie",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    verbose_name="Wyznanie",
    related_name="osoby"
)

    uwagi = models.TextField(blank=True)

    class Meta:
        ordering = ["nazwisko", "imie_pierwsze", "data_urodzenia"]
        indexes = [
            models.Index(fields=["nazwisko"]),
            models.Index(fields=["data_urodzenia"]),
        ]
        verbose_name = "Osoba"
        verbose_name_plural = "Osoby"

    def ma_komunie(self):
     
        return False

    def ma_bierzmowanie(self):
        
        return False

    def ma_malzenstwo(self):
      
        return False

    def ma_namaszczenie(self):
        
        return False

    def ma_zgon(self):
        
        return False

    def __str__(self):
        return f"{self.nazwisko} {self.imie_pierwsze}"

    def get_absolute_url(self):
        return reverse("osoba_szczegoly", args=[self.pk])
    
    
