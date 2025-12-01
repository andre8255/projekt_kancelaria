# msze/forms.py
from django import forms
from django.utils import timezone
from .models import Msza, IntencjaMszy, TypMszy
from slowniki.models import Duchowny

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

class MszaForm(BootstrapFormMixin, forms.ModelForm):
    celebrans = forms.ModelChoiceField(
        queryset=Duchowny.objects.filter(aktywny=True).order_by("imie_nazwisko"),
        required=False,
        label="Celebrans (z listy)",
        empty_label="--- wybierz ---"
    )

    class Meta:
        model = Msza
        fields = [
            "data",
            "godzina",
            "typ",
            "miejsce",
            "celebrans",
            "celebrans_opis",
            "uwagi",
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "godzina": forms.TimeInput(attrs={"type": "time"}, format="%Y-%m-%d"),
            "uwagi": forms.Textarea(attrs={"rows":3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data"].input_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"]
        self.fields["godzina"].input_formats = ["%H:%M"]

        today_str = timezone.localdate().strftime('%Y-%m-%d')
        self.fields['data'].widget.attrs['min'] = today_str

    def clean(self):
        cleaned_data = super().clean()
        
        # 1. Logika celebransa
        celebrans = cleaned_data.get("celebrans")
        opis = cleaned_data.get("celebrans_opis")
        if celebrans and opis:
            cleaned_data["celebrans_opis"] = ""

        # 2. WALIDACJA MSZY NIEDZIELNEJ
        typ = cleaned_data.get("typ")
        data = cleaned_data.get("data")

        # Sprawdzamy czy wybrano typ "Niedzielna" i czy data jest poprawna
        if typ == TypMszy.NIEDZIELNA and data:
            # Python: 0=Poniedziałek, ..., 6=Niedziela
            if data.weekday() != 6:
                self.add_error(
                    "data", 
                    "Wybrano typ 'Niedzielna', ale ta data nie przypada w niedzielę."
                )
        
        return cleaned_data

    def clean_data(self):
        data = self.cleaned_data.get('data')
        if data:
            today = timezone.localdate()
            if data < today:
                raise forms.ValidationError("Data mszy nie może być wcześniejsza niż dzisiejsza.")
        return data

class IntencjaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = IntencjaMszy
        fields = [
            "tresc",
            "zamawiajacy",
            "ofiara",
            "uwagi",
        ]
        widgets = {
            "tresc": forms.Textarea(attrs={"rows":3}),
            "uwagi": forms.Textarea(attrs={"rows":3}),
        }