# osoby/models.py
from django.db import models
from django.urls import reverse
from django.apps import apps


class Osoba(models.Model):
    nazwisko = models.CharField(max_length=30)
    imie_pierwsze = models.CharField("Imię", max_length=30)
    imie_drugie = models.CharField(max_length=30, blank=True)
    nazwisko_rodowe = models.CharField(max_length=30, blank=True)

    imie_ojca = models.CharField(max_length=30, blank=True)
    imie_matki = models.CharField(max_length=30, blank=True)

    nazwisko_ojca = models.CharField("Nazwisko ojca", max_length=30, blank=True)
    nazwisko_matki = models.CharField(
        "Nazwisko matki (aktualne)",
        max_length=30,
        blank=True,
    )
    nazwisko_matki_rodowe = models.CharField(
        "Nazwisko rodowe matki",
        max_length=30,
        blank=True,
    )

    imie_bierzmowanie = models.CharField(
        "Imię z bierzmowania",
        max_length=30,
        blank=True,
        help_text="Imię przyjęte przy bierzmowaniu (jeśli dotyczy).",
    )

    data_urodzenia = models.DateField()
    miejsce_urodzenia = models.CharField(max_length=30, blank=True)

    data_zgonu = models.DateField(null=True, blank=True)

    ulica = models.CharField(max_length=30, blank=True)
    nr_domu = models.CharField(max_length=4, blank=True)
    nr_mieszkania = models.CharField(max_length=4, blank=True)
    kod_pocztowy = models.CharField(max_length=8, blank=True)
    miejscowosc = models.CharField(max_length=30, blank=True)
    poczta = models.CharField(max_length=30, blank=True)

    telefon = models.CharField(max_length=415, blank=True)
    email = models.EmailField(blank=True)

    wyznanie = models.ForeignKey(
        "slowniki.Wyznanie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Wyznanie",
        related_name="osoby",
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

    # ==========================
    #  METODY POMOCNICZE "ma_…"
    # ==========================

    def ma_komunie(self) -> bool:
        """
        Czy osoba ma wpis I Komunii Świętej?
        Korzysta z related_name='komunie' w PierwszaKomunia.
        """
        return self.komunie.exists()

    def ma_bierzmowanie(self) -> bool:
        """
        Czy osoba ma wpis bierzmowania?
        Korzysta z related_name='bierzmowania' w Bierzmowanie.
        """
        return self.bierzmowania.exists()

    def ma_malzenstwo(self) -> bool:
        """
        Czy osoba ma jakikolwiek wpis małżeństwa
        (jako małżonek A lub jako małżonek B)?
        related_name:
          - malzenstwa_jako_a
          - malzenstwa_jako_b
        """
        return (
            self.malzenstwa_jako_a.exists()
            or self.malzenstwa_jako_b.exists()
        )

    def ma_namaszczenie(self) -> bool:
        """
        Czy osoba ma jakąkolwiek posługę / namaszczenie chorych?
        Korzysta z related_name='namaszczenia' w NamaszczenieChorych.
        """
        return self.namaszczenia.exists()

    def ma_zgon(self) -> bool:
        """
        Czy osoba jest zmarła wg danych systemu?

        Logika:
        - jeśli ma ustawioną data_zgonu -> True
        - albo jeśli istnieje wpis Zgon powiązany z osobą
          (OneToOneField related_name='zgon').
        """
        if self.data_zgonu:
            return True

        Zgon = apps.get_model("sakramenty", "Zgon")
        return Zgon.objects.filter(osoba=self).exists()

    # ==========================
    #  INNE
    # ==========================

    def __str__(self) -> str:
        return f"{self.nazwisko} {self.imie_pierwsze}"

    def get_absolute_url(self):
        return reverse("osoba_szczegoly", args=[self.pk])
