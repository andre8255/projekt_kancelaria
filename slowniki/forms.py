# slowniki/forms.py
import re

from django import forms

from .models import Duchowny, Parafia, Wyznanie


class BootstrapFormMixin:
    """
    Mixin dodający klasy Bootstrapa do pól formularza.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget

            if widget.__class__.__name__ in [
                "CheckboxInput",
                "RadioSelect",
                "CheckboxSelectMultiple",
            ]:
                widget.attrs.setdefault("class", "form-check-input")
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()

            if not widget.attrs.get("placeholder") and field.label:
                widget.attrs["placeholder"] = field.label


class ParafiaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Parafia
        fields = [
            "nazwa",
            "miejscowosc",
            "diecezja",
            "ulica",
            "nr_domu",
            "nr_mieszkania",
            "kod_pocztowy",
            "poczta",
            "telefon",
            "email",
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
            if not re.match(r"^\d{2}-\d{3}$", kod):
                self.add_error(
                    "kod_pocztowy",
                    "Kod pocztowy musi mieć format XX-XXX (np. 00-001).",
                )

        # --- 2. Walidacja Nr Domu ---
        # Reguła: Pierwszy znak to cyfra (1-9), potem cyfry, litery lub '/'
        nr_domu = cleaned_data.get("nr_domu")
        if nr_domu:
            wzorzec_dom = r"^[1-9][0-9a-zA-Z/]*$"
            if not re.match(wzorzec_dom, nr_domu):
                self.add_error(
                    "nr_domu",
                    "Musi zaczynać się od cyfry (nie 0). Dozwolone tylko litery, cyfry i znak '/'.",
                )

        # --- 3. Walidacja Nr Mieszkania ---
        # Reguła: Pierwszy znak to cyfra (0-9), potem cyfry, litery lub '/'
        nr_mieszkania = cleaned_data.get("nr_mieszkania")
        if nr_mieszkania:
            wzorzec_mieszkanie = r"^[0-9][0-9a-zA-Z/]*$"
            if not re.match(wzorzec_mieszkanie, nr_mieszkania):
                self.add_error(
                    "nr_mieszkania",
                    "Musi zaczynać się od cyfry (może być 0). Dozwolone tylko litery, cyfry i znak '/'.",
                )

        # --- 4. Walidacja Telefonu ---
        telefon = cleaned_data.get("telefon")
        if telefon:
            # Sprawdzamy czy ciąg znaków składa się tylko z cyfr
            if not telefon.isdigit():
                self.add_error(
                    "telefon",
                    "Numer telefonu może składać się wyłącznie z cyfr (bez spacji, myślników i +).",
                )

        return cleaned_data


class DuchownyForm(BootstrapFormMixin, forms.ModelForm):
    TYTUL_CHOICES = [
        ("", "— wybierz tytuł —"),
        ("ks.", "ks."),
        ("bisk.", "bisk."),
        ("prob.", "prob."),
        ("wik.", "wik."),
        ("dziek.", "dziek."),
        ("abp", "abp."),
        ("kard.", "kard."),
        ("pap.", "pap."),
    ]

    tytul = forms.ChoiceField(
        choices=TYTUL_CHOICES,
        required=False,
        label="Tytuł",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Duchowny
        fields = ["tytul", "imie_nazwisko", "parafia", "aktywny", "uwagi"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # parafia – pod Tom Select
        if "parafia" in self.fields:
            css = self.fields["parafia"].widget.attrs.get("class", "")
            self.fields["parafia"].widget.attrs["class"] = (css + " js-tom-parafia").strip()


class WyznanieForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Wyznanie
        fields = ["nazwa"]
