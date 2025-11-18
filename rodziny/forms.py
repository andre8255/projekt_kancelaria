# rodziny/forms.py
import re
from django import forms
from .models import Rodzina, CzlonkostwoRodziny
from osoby.models import Osoba

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

class RodzinaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Rodzina
        fields = [
            "nazwa",
            "ulica",
            "nr_domu",
            "nr_mieszkania",
            "kod_pocztowy",
            "miejscowosc",
            "poczta",
            "telefon_kontaktowy",
            "email_kontaktowy",
            "uwagi",
        ]
        widgets = {
            "uwagi": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # --- 1. Walidacja Kodu Pocztowego ---
        kod = cleaned_data.get("kod_pocztowy")
        if kod:
            if not re.match(r'^\d{2}-\d{3}$', kod):
                self.add_error("kod_pocztowy", "Kod pocztowy musi mieć format XX-XXX (np. 00-001).")

        # --- 2. Walidacja Nr Domu ---
        # Musi zaczynać się od 1-9 (nie zero)
        nr_domu = cleaned_data.get("nr_domu")
        if nr_domu:
            wzorzec_dom = r'^[1-9][0-9a-zA-Z/]*$'
            if not re.match(wzorzec_dom, nr_domu):
                self.add_error("nr_domu", "Musi zaczynać się od cyfry (nie 0). Dozwolone tylko litery, cyfry i znak '/'.")

        # --- 3. Walidacja Nr Mieszkania ---
        # Może zaczynać się od 0-9 (zero dozwolone)
        nr_mieszkania = cleaned_data.get("nr_mieszkania")
        if nr_mieszkania:
            wzorzec_mieszkanie = r'^[0-9][0-9a-zA-Z/]*$' # <--- ZMIANA
            if not re.match(wzorzec_mieszkanie, nr_mieszkania):
                self.add_error("nr_mieszkania", "Musi zaczynać się od cyfry (może być 0). Dozwolone tylko litery, cyfry i znak '/'.")

        return cleaned_data

class DodajCzlonkaForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formularz do dodawania istniejącej osoby do rodziny.
    """
    osoba = forms.ModelChoiceField(
        queryset=Osoba.objects.all().order_by("nazwisko", "imie_pierwsze"),
        label="Wybierz osobę",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = CzlonkostwoRodziny
        fields = ["osoba", "rola", "status", "uwagi"]
        widgets = {
            "uwagi": forms.Textarea(attrs={"rows": 2}),
        }