from django import forms
from .models import Msza, IntencjaMszy

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
    class Meta:
        model = Msza
        fields = [
            "data",
            "godzina",
            "miejsce",
            "celebrans",
            "uwagi",
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "godzina": forms.TimeInput(attrs={"type": "time"}, format="%Y-%m-%d"),
            "uwagi": forms.Textarea(attrs={"rows":3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # zaakceptuj też polskie formaty przy edycji
        self.fields["data"].input_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"]
        self.fields["godzina"].input_formats = ["%H:%M"]

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
