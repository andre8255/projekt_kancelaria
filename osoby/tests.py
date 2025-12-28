# osoby/tests.py
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from osoby.models import Osoba


class OsobaModelTest(TestCase):
    def test_str_representation(self):
        osoba = Osoba.objects.create(
            nazwisko="Kowalski",
            imie_pierwsze="Jan",
            data_urodzenia=date(2000, 1, 1),
        )
        self.assertEqual(str(osoba), "Kowalski Jan")

    def test_get_absolute_url(self):
        osoba = Osoba.objects.create(
            nazwisko="Nowak",
            imie_pierwsze="Anna",
            data_urodzenia=date(1999, 5, 10),
        )
        self.assertEqual(osoba.get_absolute_url(), reverse("osoba_szczegoly", args=[osoba.pk]))


class OsobaListaViewSearchTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="haslo123")
        self.client.login(username="tester", password="haslo123")

        Osoba.objects.create(nazwisko="Kowalski", imie_pierwsze="Jan", data_urodzenia=date(2001, 1, 1))
        Osoba.objects.create(nazwisko="Nowak", imie_pierwsze="Anna", data_urodzenia=date(2002, 2, 2))

    def test_search_filters_queryset(self):
        url = reverse("osoba_lista")

        resp = self.client.get(url, {"q": "Kowalski"})
        self.assertEqual(resp.status_code, 200)

        osoby = resp.context["osoby"]
        self.assertEqual(osoby.count(), 1)
        self.assertEqual(osoby.first().nazwisko, "Kowalski")
