# rodziny/forms.py
import re

from django import forms

from .models import Rodzina, CzlonkostwoRodziny, WizytaDuszpasterska
from osoby.models import Osoba
from slowniki.models import Duchowny


class BootstrapFormMixin:
    """
    Mixin: automatycznie dodaje klasę 'form-control' do pól formularza
    (z wyjątkiem pól typu checkbox / radio).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget
            widget_class_name = widget.__class__.__name__

            if widget_class_name in ["CheckboxInput", "RadioSelect", "CheckboxSelectMultiple"]:
                widget.attrs.setdefault("class", "form-check-input")
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()

            # domyślny placeholder = label, jeśli nie ustawiono
            if not widget.attrs.get("placeholder") and field.label:
                widget.attrs["placeholder"] = field.label


class OsobaChoiceField(forms.ModelChoiceField):
    """
    Pole ModelChoiceField z ładniejszą etykietą:
    'Kowalski Jan (dd.mm.rrrr)'.
    """

    def label_from_instance(self, obj: Osoba) -> str:
        if obj.data_urodzenia:
            return f"{obj.nazwisko} {obj.imie_pierwsze} ({obj.data_urodzenia:%d.%m.%Y})"
        return f"{obj.nazwisko} {obj.imie_pierwsze}"


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
            "telefon_kontaktowy": forms.TextInput(attrs={"placeholder": "Numer telefonu"}),
            "email_kontaktowy": forms.TextInput(attrs={"placeholder": "Adres e-mail"}),
            "uwagi": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # --- 1. Walidacja kodu pocztowego ---
        kod = cleaned_data.get("kod_pocztowy")
        if kod and not re.match(r"^\d{2}-\d{3}$", kod):
            self.add_error(
                "kod_pocztowy",
                "Kod pocztowy musi mieć format XX-XXX (np. 00-001).",
            )

        # --- 2. Walidacja nr domu ---
        # Reguła: musi zaczynać się od cyfry 1–9 (nie 0).
        nr_domu = cleaned_data.get("nr_domu")
        if nr_domu:
            wzorzec_dom = r"^[1-9][0-9a-zA-Z/]*$"
            if not re.match(wzorzec_dom, nr_domu):
                self.add_error(
                    "nr_domu",
                    "Musi zaczynać się od cyfry (nie 0). "
                    "Dozwolone tylko litery, cyfry i znak '/'.",
                )

        # --- 3. Walidacja nr mieszkania ---
        # Reguła: musi zaczynać się od cyfry 0–9 (może być 0).
        nr_mieszkania = cleaned_data.get("nr_mieszkania")
        if nr_mieszkania:
            wzorzec_mieszkanie = r"^[0-9][0-9a-zA-Z/]*$"
            if not re.match(wzorzec_mieszkanie, nr_mieszkania):
                self.add_error(
                    "nr_mieszkania",
                    "Musi zaczynać się od cyfry (może być 0). "
                    "Dozwolone tylko litery, cyfry i znak '/'.",
                )

        # --- 4. Walidacja telefonu ---
        telefon = cleaned_data.get("telefon_kontaktowy")
        if telefon and not telefon.isdigit():
            self.add_error(
                "telefon_kontaktowy",
                "Numer telefonu może składać się wyłącznie z cyfr "
                "(bez spacji, myślników i +).",
            )

        return cleaned_data


class DodajCzlonkaForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formularz do dodawania istniejącej osoby do konkretnej rodziny.
    Rodzina jest przekazywana z widoku przez parametr 'rodzina'.
    """

    osoba = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by("nazwisko", "imie_pierwsze"),
        label="Wybierz osobę",
        widget=forms.Select(attrs={"class": "js-osoba-select"}),
    )

    class Meta:
        model = CzlonkostwoRodziny
        fields = ["osoba", "rola", "status", "uwagi"]
        widgets = {
            "uwagi": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        # rodzina podana z widoku (patrz: get_form_kwargs w DodajCzlonkaView)
        self.rodzina = kwargs.pop("rodzina", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        osoba = cleaned_data.get("osoba")

        # Jeśli mamy rodzinę i osobę – sprawdzamy duplikat
        if self.rodzina and osoba:
            qs = CzlonkostwoRodziny.objects.filter(
                rodzina=self.rodzina,
                osoba=osoba,
            )

            # jeśli formularz byłby używany także do edycji – pomijamy bieżący rekord
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                # błąd „globalny” formularza – pokaże się w {{ form.non_field_errors }}
                raise forms.ValidationError(
                    "Ta osoba jest już przypisana do tej rodziny."
                )

        return cleaned_data


class WizytaForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formularz wizyty duszpasterskiej (kolędy).
    """

    ksiadz = forms.ModelChoiceField(
        queryset=Duchowny.objects.filter(aktywny=True).order_by("imie_nazwisko"),
        required=False,
        label="Ksiądz odwiedzający",
        widget=forms.Select(attrs={"class": "js-tom-duchowny"}),
    )

    class Meta:
        model = WizytaDuszpasterska
        fields = ["rok", "data_wizyty", "ksiadz", "status", "notatka"]
        widgets = {
            "data_wizyty": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "notatka": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # poprawne formaty odczytu z POST dla <input type="date">
        self.fields["data_wizyty"].input_formats = [
            "%Y-%m-%d",  # HTML5 date
            "%d.%m.%Y",
            "%d-%m-%Y",
        ]

        # dopinka klasy JS do księdza (Tom Select)
        if "ksiadz" in self.fields:
            w = self.fields["ksiadz"].widget
            css = w.attrs.get("class", "")
            w.attrs["class"] = (css + " js-tom-duchowny").strip()
