# rodziny/tests.py
from datetime import date

from django.db.utils import IntegrityError
from django.test import TestCase

from osoby.models import Osoba
from rodziny.models import Rodzina, CzlonkostwoRodziny


class RodzinyRelacjeTest(TestCase):
    def setUp(self):
        self.osoba = Osoba.objects.create(
            nazwisko="Kowalski",
            imie_pierwsze="Jan",
            data_urodzenia=date(2000, 1, 1),
        )
        self.rodzina = Rodzina.objects.create(
            nazwa="Rodzina Kowalskich",
            miejscowosc="Mykanów",
            ulica="Cicha",
            nr_domu="1",
        )

    def test_unique_membership_prevents_duplicates(self):
        CzlonkostwoRodziny.objects.create(rodzina=self.rodzina, osoba=self.osoba)

        # Ponowne przypisanie tej samej osoby do tej samej rodziny powinno zostać zablokowane
        with self.assertRaises(IntegrityError):
            CzlonkostwoRodziny.objects.create(rodzina=self.rodzina, osoba=self.osoba)
