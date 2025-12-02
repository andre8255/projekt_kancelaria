# osoby/forms.py
import re
from django.utils import timezone
from django import forms
from .models import Osoba
from slowniki.models import Wyznanie 

class BootstrapFormMixin:
    """
    Automatycznie dodaje klasę 'form-control' do pól formularza.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if widget.__class__.__name__ in ["CheckboxInput", "RadioSelect", "CheckboxSelectMultiple"]:
                widget.attrs.setdefault("class", "form-check-input")
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()
            if not widget.attrs.get("placeholder") and field.label:
                widget.attrs["placeholder"] = field.label

class OsobaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Osoba
        fields = [
            "imie_pierwsze",
            "imie_drugie",
            "imie_bierzmowanie",
            "nazwisko",
            "nazwisko_rodowe",
            "imie_ojca",
            "nazwisko_ojca",
            "imie_matki",
            "nazwisko_matki",
            "nazwisko_matki_rodowe",
            "data_urodzenia",
            "miejsce_urodzenia",
            "wyznanie",
            "data_zgonu",

            "ulica",
            "nr_domu",
            "nr_mieszkania",
            "kod_pocztowy",
            "miejscowosc",
            "poczta",

            "telefon",
            "email",
            "uwagi",
        ]
        widgets = {
           # Wymuszamy format Y-m-d, żeby data nie znikała przy edycji
           "data_urodzenia": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
           "data_zgonu": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
           "uwagi": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "wyznanie" in self.fields:
            widget = self.fields["wyznanie"].widget
            css = widget.attrs.get("class", "")
            widget.attrs["class"] = (css + " js-tom-wyznanie").strip()
            widget.attrs.setdefault("placeholder", "Wpisz nazwę wyznania...")
            
        self.fields["wyznanie"].label = "Wyznanie"
        self.fields["wyznanie"].queryset = Wyznanie.objects.all().order_by("nazwa")
        self.fields["wyznanie"].required = False
        self.fields["wyznanie"].empty_label = "— wybierz —"

    def clean(self):
        """
        Wspólna walidacja dla całego formularza.
        """
        cleaned_data = super().clean()
        today = timezone.localdate()

        # --- 1. Walidacja Daty Urodzenia i Zgonu ---
        data_ur = cleaned_data.get("data_urodzenia")
        data_zg = cleaned_data.get("data_zgonu")

        if data_ur and data_ur > today:
            self.add_error("data_urodzenia", "Data urodzenia nie może być z przyszłości.")
        
        if data_zg:
            if data_zg > today:
                 self.add_error("data_zgonu", "Data zgonu nie może być z przyszłości.")
            if data_ur and data_zg < data_ur:
                 self.add_error("data_zgonu", "Data zgonu nie może być wcześniejsza niż data urodzenia.")

        # --- 2. Walidacja Kodu Pocztowego ---
        kod = cleaned_data.get("kod_pocztowy")
        if kod:
            # Wzorzec: 2 cyfry, myślnik, 3 cyfry
            if not re.match(r'^\d{2}-\d{3}$', kod):
                self.add_error("kod_pocztowy", "Kod pocztowy musi mieć format XX-XXX (np. 00-001).")

        # --- 3. Walidacja Nr Domu ---
        # Reguła: Musi zaczynać się od cyfry 1-9 (nie może być 0).
        nr_domu = cleaned_data.get("nr_domu")
        if nr_domu:
            wzorzec_dom = r'^[1-9][0-9a-zA-Z/]*$'
            if not re.match(wzorzec_dom, nr_domu):
                self.add_error("nr_domu", "Musi zaczynać się od cyfry (nie 0). Dozwolone tylko litery, cyfry i znak '/'.")

        # --- 4. Walidacja Nr Mieszkania ---
        # Reguła: Musi zaczynać się od cyfry 0-9 (MOŻE być 0).
        nr_mieszkania = cleaned_data.get("nr_mieszkania")
        if nr_mieszkania:
            wzorzec_mieszkanie = r'^[0-9][0-9a-zA-Z/]*$'
            if not re.match(wzorzec_mieszkanie, nr_mieszkania):
                self.add_error("nr_mieszkania", "Musi zaczynać się od cyfry (może być 0). Dozwolone tylko litery, cyfry i znak '/'.")

        # --- 5. Walidacja Telefonu ---
        telefon = cleaned_data.get("telefon")
        if telefon:
            # Sprawdzamy czy ciąg znaków składa się tylko z cyfr
            if not telefon.isdigit():
                self.add_error("telefon", "Numer telefonu może składać się wyłącznie z cyfr (bez spacji, myślników i +).")

        return cleaned_data