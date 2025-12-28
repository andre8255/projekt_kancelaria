from django.db import models

class Parafia(models.Model):
    nazwa = models.CharField(
        "Nazwa parafii",
        max_length=200,
        help_text="Np. Parafia św. Jana Chrzciciela"
    )
    miejscowosc = models.CharField(
        "Miejscowość",
        max_length=120,
        blank=True
    )
    diecezja = models.CharField(
        "Diecezja",
        max_length=120,
        blank=True
    )
    
    ulica = models.CharField(
        "Ulica",
        max_length=120,
        blank=True
    )
    nr_domu = models.CharField(
        "Nr domu",
        max_length=30,
        blank=True
    )
    nr_mieszkania = models.CharField(
        "Nr mieszkania",
        max_length=30,
        blank=True
    )
    kod_pocztowy = models.CharField(
        "Kod pocztowy",
        max_length=15,
        blank=True
    )
    poczta = models.CharField(
        "Poczta",
        max_length=120,
        blank=True
    )

    # --- Kontakt ---
    telefon = models.CharField(
        "Telefon",
        max_length=40,
        blank=True
    )
    email = models.EmailField(
        "Email",
        blank=True
    )
    uwagi = models.TextField(
        "Uwagi",
        blank=True,
        help_text="Np. dekanat, status, uwagi własne"
    )

    class Meta:
        verbose_name = "Parafia"
        verbose_name_plural = "Parafie"
        ordering = ["miejscowosc", "nazwa"]

    def __str__(self):
        if self.miejscowosc:
            return f"{self.miejscowosc} – {self.nazwa}"
        return self.nazwa


class Duchowny(models.Model):
    TYTUL_CHOICES = [
        ("ks.", "ks."),
        ("bisk.", "bisk."),
        ("prob.", "prob."),
        ("wik.", "wik."),
        ("dziek.", "dziek."),
        ("abp.", "abp."),
        ("kard.", "kard."),
        ("pap.", "pap."),
    ]

    tytul = models.CharField(
        "Tytuł",
        max_length=20,
        choices=TYTUL_CHOICES,
        blank=True,
        help_text="Np. ks., biskp, prob."
    )

    imie_nazwisko = models.CharField(
        "Imię i nazwisko",
        max_length=200,
        help_text="Np. Jan Kowalski"
    )

    parafia = models.ForeignKey(
        Parafia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duchowni",
        verbose_name="Parafia posługi",
        help_text="Parafia, w której posługiwał przy sakramencie"
    )

    aktywny = models.BooleanField(
        "Aktywny",
        default=True,
        help_text="Odznacz jeśli już nie posługuje, ale chcesz go mieć do historii"
    )

    uwagi = models.TextField(
        "Uwagi",
        blank=True,
        help_text="Np. proboszcz, wikariusz, biskup pomocniczy"
    )

    class Meta:
        verbose_name = "Duchowny"
        verbose_name_plural = "Duchowni"
        ordering = ["imie_nazwisko"]

    def __str__(self):
        if self.tytul:
            return f"{self.tytul} {self.imie_nazwisko}"
        return self.imie_nazwisko


class Wyznanie(models.Model):
    nazwa = models.CharField(
        "Nazwa wyznania",
        max_length=200,
        unique=True,
        help_text='Np. "rzymskokatolickie", "prawosławne", "ewangelickie", "brak"'
    )

    aktywne = models.BooleanField(
        "Aktywne",
        default=True,
        help_text="Jeśli odznaczone, nie pokazuje się przy dodawaniu nowych osób."
    )

    class Meta:
        verbose_name = "Wyznanie"
        verbose_name_plural = "Wyznania"
        ordering = ["nazwa"]

    def __str__(self):
        return self.nazwa
