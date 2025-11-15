# rodziny/forms.py
from django import forms
from .models import Rodzina, CzlonkostwoRodziny
from osoby.models import Osoba

class BootstrapFormMixin:
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



class RodzinaForm(BootstrapFormMixin,forms.ModelForm):
    class Meta:
        model = Rodzina
        fields = [
            "nazwa",
            "ulica", "nr_domu", "nr_mieszkania",
            "kod_pocztowy", "miejscowosc", "poczta",
            "telefon_kontaktowy", "email_kontaktowy",
            "uwagi",
        ]
        widgets = {
            "uwagi": forms.Textarea(attrs={"rows":3})
        }

class DodajCzlonkaForm(BootstrapFormMixin,forms.ModelForm):
    osoba = forms.ModelChoiceField(
        queryset=Osoba.objects.all().order_by("nazwisko", "imie_pierwsze"),
        label="Osoba",
        help_text="Wybierz istniejącą osobę z parafii"
    )

    class Meta:
        model = CzlonkostwoRodziny
        fields = [
            "osoba",
            "rola",
            "status",
            "uwagi",
        ]
        widgets = {
            "uwagi": forms.Textarea(attrs={"rows":3}),
        }
