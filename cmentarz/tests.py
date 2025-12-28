# cmentarz/tests.py
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from osoby.models import Osoba
from cmentarz.models import Sektor, Grob, Pochowany


class CmentarzModelTest(TestCase):
    def setUp(self):
        self.sektor = Sektor.objects.create(nazwa="A1")

    def test_unique_grob_in_sector_row_number(self):
        Grob.objects.create(sektor=self.sektor, rzad="1", numer="10")
        with self.assertRaises(IntegrityError):
            Grob.objects.create(sektor=self.sektor, rzad="1", numer="10")

    def test_auto_wazny_do_is_set_20_years(self):
        g = Grob.objects.create(
            sektor=self.sektor,
            rzad="1",
            numer="11",
            data_oplaty=date(2020, 5, 1),
            wazny_do=None,
        )
        self.assertEqual(g.wazny_do, date(2040, 5, 1))

    def test_feb29_special_case(self):
        # 2080-02-29 + 20 lat => 2100-02-28 (rok 2100 nie jest przestępny)
        g = Grob.objects.create(
            sektor=self.sektor,
            rzad="2",
            numer="1",
            data_oplaty=date(2080, 2, 29),
            wazny_do=None,
        )
        self.assertEqual(g.wazny_do, date(2100, 2, 28))

    def test_status_oplaty(self):
        dzis = timezone.localdate()

        g1 = Grob.objects.create(sektor=self.sektor, rzad="3", numer="1", wazny_do=dzis - timedelta(days=1))
        self.assertEqual(g1.status_oplaty, "EXPIRED")

        g2 = Grob.objects.create(sektor=self.sektor, rzad="3", numer="2", wazny_do=dzis + timedelta(days=100))
        self.assertEqual(g2.status_oplaty, "WARNING")

        g3 = Grob.objects.create(sektor=self.sektor, rzad="3", numer="3", wazny_do=dzis + timedelta(days=500))
        self.assertEqual(g3.status_oplaty, "OK")


class CmentarzWyszukiwanieTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="haslo123")
        self.client.login(username="tester", password="haslo123")

        self.sektor = Sektor.objects.create(nazwa="B1")
        self.grob = Grob.objects.create(sektor=self.sektor, rzad="1", numer="5")

        self.osoba = Osoba.objects.create(
            nazwisko="Zielinski",
            imie_pierwsze="Piotr",
            data_urodzenia=date(1970, 1, 1),
        )
        Pochowany.objects.create(grob=self.grob, osoba=self.osoba)

    def test_search_by_pochowany_nazwisko(self):
        url = reverse("cmentarz:grob_lista")
        resp = self.client.get(url, {"q": "Zielinski"})
        self.assertEqual(resp.status_code, 200)

        groby = resp.context["groby"]
        self.assertEqual(groby.count(), 1)
        self.assertEqual(groby.first().pk, self.grob.pk)
