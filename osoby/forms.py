# osoby/forms.py
from django import forms
from .models import Osoba
from slowniki.models import Wyznanie

class DateInput(forms.DateInput):
    input_type = "date"


class BootstrapFormMixin:
    """
    Prosty mixin: automatycznie dodaje klasę 'form-control'
    do wszystkich pól <input>, <select>, <textarea>.
    Dzięki temu formularz wygląda jak Bootstrap.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget

            # checkboxy/radiobuttony mają inny styl, nie ruszamy ich
            if widget.__class__.__name__ in ["CheckboxInput", "RadioSelect", "CheckboxSelectMultiple"]:
                widget.attrs.setdefault("class", "form-check-input")
            else:
                # zwykłe pola tekstowe, selecty, textarea
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()

            # drobne upiększenie: placeholder domyślnie = label
            if not widget.attrs.get("placeholder") and hasattr(field, "label") and field.label:
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

            "ulica",
            "nr_domu",
            "nr_mieszkania",
            "kod_pocztowy",
            "miejscowosc",
            "poczta",

            "telefon",
            "email",
        ]
        widgets = {
           "data_urodzenia": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["data_urodzenia"].input_formats = ["%Y-%m-%d"]
        # ładna etykieta
        self.fields["wyznanie"].label = "Wyznanie"

        # pobierz tylko aktywne wyznania, alfabetycznie
        self.fields["wyznanie"].queryset = Wyznanie.objects.filter(
            aktywne=True
        ).order_by("nazwa")

        # pole może być puste
        self.fields["wyznanie"].required = False
        self.fields["wyznanie"].empty_label = "— wybierz —"