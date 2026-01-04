# slowniki/tests.py
from django.test import TestCase
from slowniki.forms import ParafiaForm

class ParafiaFormValidationTest(TestCase):
    def test_invalid_postal_code(self):
        form = ParafiaForm(data={
            "nazwa": "Parafia testowa",
            "kod_pocztowy": "12345",  # zły format
        })
        self.assertFalse(form.is_valid())
        self.assertIn("kod_pocztowy", form.errors)

    def test_invalid_nr_domu(self):
        form = ParafiaForm(data={
            "nazwa": "Parafia testowa",
            "nr_domu": "0A",  # nie może zaczynać się od 0
        })
        self.assertFalse(form.is_valid())
        self.assertIn("nr_domu", form.errors)

    def test_invalid_phone(self):
        form = ParafiaForm(data={
            "nazwa": "Parafia testowa",
            "telefon": "+48 123 456 789",  # dopuszczalne są tylko cyfry
        })
        self.assertFalse(form.is_valid())
        self.assertIn("telefon", form.errors)

    def test_valid_data(self):
        form = ParafiaForm(data={
            "nazwa": "Parafia św. Jana",
            "kod_pocztowy": "42-233",
            "nr_domu": "12A",
            "telefon": "123456789",
        })
        self.assertTrue(form.is_valid(), form.errors)
