# msze/forms.py
from django import forms
from datetime import datetime
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

    MIEJSCE_CHOICES = [
        ("Kościół", "Kościół"),
        ("Kaplica", "Kaplica"),
    ]

    miejsce = forms.ChoiceField(
        label="Miejsce",
        choices=MIEJSCE_CHOICES,
        initial="Kościół",          # domyślnie „Kościół”
        widget=forms.Select(),      # zwykły <select>, BootstrapFormMixin doda klasy
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
           
            "godzina": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "uwagi": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data"].input_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"]
        self.fields["godzina"].input_formats = ["%H:%M"]

        today_str = timezone.localdate().strftime('%Y-%m-%d')
        self.fields['data'].widget.attrs['min'] = today_str

        if "celebrans" in self.fields:
            widget = self.fields["celebrans"].widget
            css = widget.attrs.get("class", "")
            widget.attrs["class"] = (css + " js-tom-duchowny").strip()
            widget.attrs.setdefault("placeholder", "Wpisz nazwisko duchownego...")

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

        if typ == TypMszy.NIEDZIELNA and data:
            # 0=pn ... 6=nd
            if data.weekday() != 6:
                self.add_error(
                    "data",
                    "Wybrano typ 'Niedzielna', ale ta data nie przypada w niedzielę."
                )


    # 3. WALIDACJA: data + godzina nie mogą być w przeszłości
        data = cleaned_data.get("data")
        godzina = cleaned_data.get("godzina")

        if data and godzina:
            dt = datetime.combine(data, godzina)
            # Upewniamy się, że jest to datetime z timezone
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())

            teraz = timezone.now()
            if dt < teraz:
                self.add_error("data", "Data i godzina mszy nie mogą być w przeszłości.")
                self.add_error("godzina", "Data i godzina mszy nie mogą być w przeszłości.")

        return cleaned_data


class IntencjaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = IntencjaMszy
        # UWAGA: bez pola "ofiara", z nowym polem "status_oplaty"
        fields = ["tresc", "zamawiajacy", "status_oplaty", "uwagi"]
        widgets = {
            "tresc": forms.Textarea(attrs={"rows": 3}),
             "zamawiajacy": forms.TextInput(attrs={"placeholder": "Imię i nazwisko"}),
            "status_oplaty": forms.Select(),
            "uwagi": forms.Textarea(attrs={"rows": 2}),
        }
