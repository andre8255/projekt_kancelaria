#sakramenty/models.py
from django.db import models
from django.urls import reverse
from osoby.models import Osoba
from slowniki.models import Parafia, Duchowny,Wyznanie

class Chrzest(models.Model):
    # Identyfikacja w księdze
    rok = models.PositiveIntegerField(
        "Rok",
        help_text="Rok księgi chrztów (np. 2025)"
    )
    akt_nr = models.CharField(
        "Nr aktu",
        max_length=20,
        help_text="Numer aktu chrztu w danym roku"
    )

    # Osoba
    ochrzczony = models.ForeignKey(
        Osoba,
        on_delete=models.CASCADE,
        related_name="chrzty",
        verbose_name="Ochrzczony/a"
    )

    # Dane o urodzeniu
    data_urodzenia = models.DateField(
        "Data urodzenia",
        null=True,
        blank=True
    )
    rok_urodzenia = models.PositiveIntegerField(
        "Rok urodzenia (jeśli brak pełnej daty)",
        null=True,
        blank=True,
        help_text="Wpisz tylko rok, jeśli nie znasz dokładnej daty urodzenia"
    )
    miejsce_urodzenia = models.CharField(
        "Miejsce urodzenia",
        max_length=200,
        blank=True
    )

    # Dane o chrzcie
    data_chrztu = models.DateField(
        "Data chrztu (pełna)",
        null=True,
        blank=True,
        help_text="Pełna data (dzień-miesiąc-rok), jeśli znana"
    )
    rok_chrztu = models.PositiveIntegerField(
        "Rok chrztu",
        null=True,
        blank=True,
        help_text="Wpisz tylko rok, jeśli nie znasz pełnej daty chrztu"
    )
    miejsce_chrztu = models.CharField(
        "Miejsce chrztu",
        max_length=200,
        blank=True,
        help_text=""
    )

    # Rodzice
    ojciec = models.CharField(
        "Ojciec (imię i nazwisko)",
        max_length=200,
        blank=True
    )
    ojciec_wyznanie = models.ForeignKey(
    Wyznanie,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    verbose_name="Ojciec - wyznanie",
    related_name="ojcowie_przy_chrzcie"
)

    matka = models.CharField(
        "Matka (imię i nazwisko)",
        max_length=200,
        blank=True
    )
    nazwisko_matki_rodowe = models.CharField(
        "Nazwisko rodowe matki",
        max_length=200,
        blank=True
    )
    matka_wyznanie = models.ForeignKey(
    Wyznanie,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    verbose_name="Matka - wyznanie",
    related_name="matki_przy_chrzcie"
)

    # Uwagi kancelaryjne (dla nas, nie drukuje się na świadectwie)
    uwagi_wew = models.TextField(
        "Uwagi kancelaryjne (wewnętrzne)",
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ochrzczony"],
                name="unique_chrzest_per_osoba",
            ),
            models.UniqueConstraint(
                fields=["rok", "akt_nr"],
                name="unique_chrzest_rok_akt",
            ),
        ]

        verbose_name = "Chrzest"
        verbose_name_plural = "Chrzty"
        ordering = ["-rok", "akt_nr"]
        indexes = [
            models.Index(fields=["rok"]),
            models.Index(fields=["akt_nr"]),
        ]
        unique_together = [("rok", "akt_nr")]

    def __str__(self):
        return f"Chrzest {self.rok}/{self.akt_nr} – {self.ochrzczony}"

    def get_absolute_url(self):
        return reverse("chrzest_szczegoly", args=[self.pk])


class PierwszaKomunia(models.Model):
    """
    I Komunia Święta
    -> rok komunii (wystarczy sam rok)
    -> parafia (gdzie przyjęta)
    """
    osoba = models.ForeignKey(
        Osoba,
        on_delete=models.CASCADE,
        related_name="komunie",
        verbose_name="Osoba"
    )

    rok = models.CharField(
        "Rok I Komunii",
        max_length=10,
        blank=True,
        help_text="Np. 1998"
    )

    # Parafia może być słownikowa ALBO wpisana ręcznie
    parafia = models.ForeignKey(
        "slowniki.Parafia",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="komuni",
        verbose_name="Parafia I komuni św."
    )

    uwagi_wew = models.TextField(
        "Uwagi kancelaryjne (wewnętrzne)",
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["osoba"],
                name="unique_komunia_per_osoba",
            ),
        ]
        verbose_name = "I Komunia Święta"
        verbose_name_plural = "I Komunie Święte"
        ordering = ["rok", "osoba__nazwisko", "osoba__imie_pierwsze"]

    def __str__(self):
        return f"I Komunia {self.osoba} ({self.rok})"

    def get_absolute_url(self):
        # możesz zrobić docelowo stronę szczegółów Komunii
        return reverse("osoba_szczegoly", args=[self.osoba.pk])


class Bierzmowanie(models.Model):
    osoba = models.ForeignKey(
        "osoby.Osoba",
        on_delete=models.CASCADE,
        related_name="bierzmowania",
        verbose_name="Osoba"
    )

    rok = models.CharField(
        "Rok bierzmowania",
        max_length=10,
        blank=True,
        help_text="Np. 2005"
    )

    akt_nr = models.CharField(
        "Nr aktu bierzmowania",
        max_length=20,
        blank=True,
        help_text="Numer aktu w księdze bierzmowania"
    )

    data_bierzmowania = models.DateField(
        "Data bierzmowania (pełna)",
        null=True,
        blank=True,
        help_text="Pełna data (dzień-miesiąc-rok)"
    )

    # <-- NOWE POLE, KTÓRE BRAKUJE -->
    imie_bierzmowania = models.CharField(
        "Imię bierzmowania",
        max_length=100,
        blank=True,
        help_text="Imię przyjęte przy bierzmowaniu"
    )

    # <-- NOWE POLE, KTÓRE BRAKUJE -->
    miejsce_bierzmowania = models.CharField(
        "Miejsce bierzmowania",
        max_length=100,
        blank=True,
        help_text="Miejsce bierzmowania"
    )



    # Parafia może być słownikowa ALBO wpisana ręcznie
    parafia = models.ForeignKey(
        "slowniki.Parafia",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bierzmowania",
        verbose_name="Parafia bierzmowania"
    )

    parafia_nazwa_reczna = models.CharField(
        "Parafia (opis ręczny)",
        max_length=200,
        blank=True,
        help_text="Jeśli nie ma na liście powyżej"
    )

    # Szafarz (biskup / ksiądz udzielający)
    szafarz = models.ForeignKey(
        "slowniki.Duchowny",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bierzmowania",
        verbose_name="Szafarz (udzielający bierzmowania)"
    )

    szafarz_opis_reczny = models.CharField(
        "Szafarz (opis ręczny)",
        max_length=200,
        blank=True,
        help_text="Np. «bp Jan Kowalski», «ks. Piotr Nowak»"
    )

    swiadek = models.CharField(
        "Świadek bierzmowania",
        max_length=200,
        blank=True,
        help_text="Imię i nazwisko świadka"
    )

    uwagi_wew = models.TextField(
        "Uwagi kancelaryjne (wewnętrzne)",
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["osoba"],
                name="unique_bierzmowanie_per_osoba",
            ),
        ]
        verbose_name = "Bierzmowanie"
        verbose_name_plural = "Bierzmowania"
        ordering = ["rok", "osoba__nazwisko", "osoba__imie_pierwsze"]

    def __str__(self):
        return f"Bierzmowanie {self.osoba} ({self.rok}/{self.akt_nr})"

    def get_absolute_url(self):
        return reverse("osoba_szczegoly", args=[self.osoba.pk])

class Malzenstwo(models.Model):
    malzonek_a = models.ForeignKey(
        "osoby.Osoba",
        on_delete=models.CASCADE,
        related_name="malzenstwa_jako_a",
        verbose_name="Małżonek A"
    )
    malzonek_b = models.ForeignKey(
        "osoby.Osoba",
        on_delete=models.CASCADE,
        related_name="malzenstwa_jako_b",
        verbose_name="Małżonek B"
    )

    rok = models.CharField(
        "Rok ślubu",
        max_length=10,
        blank=True,
        help_text="Np. 2014. Możesz wpisać tylko rok."
    )

    akt_nr = models.CharField(
        "Nr aktu małżeństwa",
        max_length=30,
        blank=True,
        help_text="Numer aktu w księdze małżeństw."
    )

    data_slubu = models.DateField(
        "Data ślubu (pełna)",
        null=True,
        blank=True
    )

    # PARAFIA
    parafia = models.ForeignKey(
        "slowniki.Parafia",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sluby",
        verbose_name="Parafia ślubu"
    )
    parafia_opis_reczny = models.CharField(
        "Parafia ślubu (opis ręczny)",
        max_length=200,
        blank=True,
        help_text="Jeśli nie ma parafii na liście powyżej, wpisz tutaj."
    )

    # DUCHOWNY (asystujący / świadek urzędowy)
    swiadek_urzedowy = models.ForeignKey(
        "slowniki.Duchowny",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sluby_asystowane",
        verbose_name="Świadek urzędowy / asystujący"
    )
    swiadek_urzedowy_opis_reczny = models.CharField(
        "Świadek urzędowy / asystujący (opis ręczny)",
        max_length=200,
        blank=True,
        help_text="Kapłan/diakon, który asystował przy zawarciu małżeństwa."
    )

    uwagi_wew = models.TextField(
        "Uwagi (wewnętrzne)",
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rok", "akt_nr"],
                name="unique_malzenstwo_rok_akt",
            ),
        ]
        verbose_name = "Małżeństwo"
        verbose_name_plural = "Małżeństwa"
        ordering = ["rok", "malzonek_a__nazwisko", "malzonek_b__nazwisko"]

    def __str__(self):
        return f"Małżeństwo: {self.malzonek_a} + {self.malzonek_b} ({self.rok}/{self.akt_nr})"



class NamaszczenieChorych(models.Model):
    """
    Posługa chorym:
    - data wizyty
    - miejsce
    - szafarz
    - czy odbyła się spowiedź / komunia / namaszczenie
    """

    osoba = models.ForeignKey(
        Osoba,
        on_delete=models.CASCADE,
        related_name="namaszczenia",
        verbose_name="Osoba"
    )

    data = models.DateField(
        "Data posługi",
        null=True,
        blank=True
    )

    miejsce = models.CharField(
        "Miejsce",
        max_length=200,
        blank=True,
        help_text="Np. dom chorego, szpital"
    )

    szafarz = models.ForeignKey(
    Duchowny,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    verbose_name="Szafarz",
    related_name="namaszczenia_udzielone"
)

    spowiedz = models.BooleanField(
        "Spowiedź",
        default=False
    )

    komunia = models.BooleanField(
        "Komunia święta",
        default=False
    )

    namaszczenie = models.BooleanField(
        "Namaszczenie chorych",
        default=False
    )

    uwagi_wew = models.TextField(
        "Uwagi duszpasterskie / stan chorego",
        blank=True
    )

    class Meta:
        verbose_name = "Namaszczenie chorych / posługa"
        verbose_name_plural = "Namaszczenia chorych / posługi"
        ordering = ["-data", "osoba__nazwisko", "osoba__imie_pierwsze"]

    def __str__(self):
        return f"Namaszczenie / posługa u {self.osoba} ({self.data})"

    def get_absolute_url(self):
        return reverse("osoba_szczegoly", args=[self.osoba.pk])


class Zgon(models.Model):
    """
    Księga zgonów:
    - rok
    - akt nr
    - dane o zgonie/pogrzebie
    - cmentarz
    Uwaga: Osoba ma tylko jeden zgon -> OneToOneField
    """

    osoba = models.OneToOneField(
        Osoba,
        on_delete=models.CASCADE,
        related_name="zgon",
        verbose_name="Zmarły/a"
    )

    rok = models.CharField(
        "Rok zgonu / księgi",
        max_length=10,
        blank=True,
        help_text="Np. 2024"
    )

    akt_nr = models.CharField(
        "Nr aktu zgonu",
        max_length=20,
        blank=True,
        help_text="Numer aktu w księdze zgonów"
    )

    data_zgonu = models.DateField(
        "Data zgonu",
        null=True,
        blank=True
    )

    miejsce_zgonu = models.CharField(
        "Miejsce zgonu",
        max_length=200,
        blank=True
    )

    data_pogrzebu = models.DateField(
        "Data pogrzebu",
        null=True,
        blank=True
    )

    cmentarz = models.CharField(
        "Cmentarz",
        max_length=200,
        blank=True
    )

    uwagi_wew = models.TextField(
        "Uwagi kancelaryjne (wewnętrzne)",
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["osoba"],
                name="unique_zgon_per_osoba",
            ),
            models.UniqueConstraint(
                fields=["rok", "akt_nr"],
                name="unique_zgon_rok_akt",
            ),
        ]
        verbose_name = "Zgon"
        verbose_name_plural = "Zgony"
        ordering = ["rok", "akt_nr"]

    def __str__(self):
        return f"Zgon {self.osoba} ({self.rok}/{self.akt_nr})"

    def get_absolute_url(self):
        return reverse("osoba_szczegoly", args=[self.osoba.pk])
