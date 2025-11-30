from django.db import models
from django.core.exceptions import ValidationError

class UstawieniaParafii(models.Model):
    """
    Model Singleton - przechowuje dane parafii do wydruków.
    W bazie może istnieć tylko jeden taki rekord.
    """
    nazwa = models.CharField("Nazwa Parafii (nagłówek)", max_length=255, default="RZYMSKOKATOLICKA PARAFIA PW. ...")
    miejscowosc = models.CharField("Miejscowość", max_length=100, default="Mykanów")
    adres = models.CharField("Adres (ulica i kod)", max_length=255, default="ul. Cicha 1, 42-233 Mykanów")
    
    # Opcjonalne pola "PRO" (Efekt WOW)
    nip = models.CharField("NIP", max_length=20, blank=True, null=True)
    regon = models.CharField("REGON", max_length=20, blank=True, null=True)
    konto_bankowe = models.CharField("Nr konta bankowego", max_length=60, blank=True, null=True)
    logo = models.ImageField("Logo / Pieczęć (do wydruków)", upload_to="konfiguracja/logo/", blank=True, null=True)

    class Meta:
        verbose_name = "Konfiguracja Parafii"
        verbose_name_plural = "Konfiguracja Parafii"

    def __str__(self):
        return "Dane Parafii (Główna konfiguracja)"

    def save(self, *args, **kwargs):
        """Blokada tworzenia drugiego rekordu."""
        if not self.pk and UstawieniaParafii.objects.exists():
            raise ValidationError("Można zdefiniować tylko jedną konfigurację parafii. Edytuj istniejącą.")
        return super(UstawieniaParafii, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Metoda pomocnicza: pobiera obiekt lub tworzy domyślny, jeśli brak."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj