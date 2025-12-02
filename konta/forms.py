# konta/forms.py
from django import forms
from .models import BackupUstawienia


class BackupUstawieniaForm(forms.ModelForm):
    class Meta:
        model = BackupUstawienia
        fields = ["wlaczony", "czestotliwosc", "dzien_tygodnia", "godzina"]
        labels = {
            "wlaczony": "Włącz automatyczne backupy",
            "czestotliwosc": "Częstotliwość",
            "dzien_tygodnia": "Dzień tygodnia (dla backupu tygodniowego)",
            "godzina": "Godzina uruchamiania",
        }
        widgets = {
            "godzina": forms.TimeInput(attrs={"type": "time"}),
        }
