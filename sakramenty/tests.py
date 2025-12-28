# sakramenty/tests.py
from datetime import date

from django.db.utils import IntegrityError
from django.test import TestCase

from osoby.models import Osoba
from sakramenty.models import Chrzest


class ChrzestConstraintsTest(TestCase):
    def setUp(self):
        self.osoba = Osoba.objects.create(
            nazwisko="Nowak",
            imie_pierwsze="Anna",
            data_urodzenia=date(2010, 3, 15),
        )

    def test_one_chrzest_per_osoba(self):
        Chrzest.objects.create(rok=2025, akt_nr="1", ochrzczony=self.osoba)

        # Drugi chrzest dla tej samej osoby powinien naruszyć constraint unique_chrzest_per_osoba
        with self.assertRaises(IntegrityError):
            Chrzest.objects.create(rok=2026, akt_nr="2", ochrzczony=self.osoba)

    def test_unique_rok_akt_nr(self):
        inna_osoba = Osoba.objects.create(
            nazwisko="Kowalski",
            imie_pierwsze="Jan",
            data_urodzenia=date(2011, 4, 20),
        )
        Chrzest.objects.create(rok=2025, akt_nr="10", ochrzczony=self.osoba)

        # Ten sam (rok, akt_nr) nie może wystąpić ponownie
        with self.assertRaises(IntegrityError):
            Chrzest.objects.create(rok=2025, akt_nr="10", ochrzczony=inna_osoba)
