# cmentarz/forms.py
from django import forms
from django.utils import timezone
from .models import Sektor, Grob, Pochowany
from osoby.models import Osoba
from sakramenty.models import Zgon 

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if widget.__class__.__name__ in ["CheckboxInput", "RadioSelect"]:
                widget.attrs.setdefault("class", "form-check-input")
            else:
                widget.attrs.setdefault("class", "form-control")

# --- 1. SPECJALNE POLE DO WYBORU OSOBY (ROZWIĄZANIE PROBLEMU DUPLIKATÓW) ---
class OsobaChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Tworzy etykietę: "Kowalski Jan (ur. 1980-01-01, o. Józefa)"
        opis = f"{obj.nazwisko} {obj.imie_pierwsze}"
        szczegoly = []
        if obj.data_urodzenia:
            szczegoly.append(f"ur. {obj.data_urodzenia}")
        
             
        if szczegoly:
            opis += f" ({', '.join(szczegoly)})"
        return opis

class SektorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Sektor
        fields = ["nazwa", "opis"]
        widgets = { "opis": forms.Textarea(attrs={"rows": 2}) }

class GrobForm(BootstrapFormMixin, forms.ModelForm):
    
    dysponent = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by('nazwisko', 'imie_pierwsze'),
        required=False,
        label="Dysponent (Opiekun)",
        widget=forms.Select(attrs={'class': 'form-select'}) # Klasa dla stylów
    )

    class Meta:
        model = Grob
        fields = ["sektor", "rzad","numer", "typ", "dysponent", "data_oplaty", "wazny_do", "uwagi", "zdjecie"]
        widgets = {
            "data_oplaty": forms.DateInput(attrs={"type": "date"}, format='%Y-%m-%d'),
            "wazny_do": forms.DateInput(attrs={"type": "date"}, format='%Y-%m-%d'),
            "uwagi": forms.Textarea(attrs={"rows": 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # jeśli BootstrapFormMixin dopisuje "form-control", ta klasa dojdzie do js-osoba-select
        if "dysponent" in self.fields:
            w = self.fields["dysponent"].widget
            css = w.attrs.get("class", "")
            w.attrs["class"] = (css + " js-osoba-select").strip()
        # to pole, na którym chce mieć „live search”
        if "osoba" in self.fields:
            css = self.fields["osoba"].widget.attrs.get("class", "")
            self.fields["osoba"].widget.attrs["class"] = (css + " js-osoba-select").strip()

    def clean(self):
        cleaned_data = super().clean()
        sektor = cleaned_data.get("sektor")
        rzad = cleaned_data.get("rzad")
        numer = cleaned_data.get("numer") or "" # Puste jako pusty string

        if self.instance.pk:
            # Edycja - wykluczamy siebie
            if Grob.objects.filter(sektor=sektor,  rzad=rzad, numer=numer).exclude(pk=self.instance.pk).exists():
                self.add_error('numer', f"Grób {rzad} (numer {numer}) w tym sektorze już istnieje.")
        else:
            # Nowy
            if Grob.objects.filter(sektor=sektor,  rzad=rzad, numer=numer).exists():
                self.add_error('numer', f"Grób {rzad} (numer {numer}) w tym sektorze już istnieje.")
        
        return cleaned_data

# --- 2. FORMULARZ POCHOWANEGO ---
class PochowanyForm(BootstrapFormMixin, forms.ModelForm):
    # Ulepszone pole wyboru
    osoba = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by('nazwisko', 'imie_pierwsze'),
        label="Wybierz osobę zmarłą",
        help_text="Lista zawiera rok urodzenia i imię ojca dla rozróżnienia."
    )
    
    data_pochowania = forms.DateField(
        label="Data pogrzebu",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format='%Y-%m-%d'),
        help_text="Jeśli puste, system spróbuje pobrać z Aktu Zgonu."
    )
    
    class Meta:
        model = Pochowany
        fields = ["osoba", "data_pochowania"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pole,  „live search”
        if "osoba" in self.fields:
            css = self.fields["osoba"].widget.attrs.get("class", "")
            self.fields["osoba"].widget.attrs["class"] = (css + " js-osoba-select").strip()

    def clean(self):
        cleaned_data = super().clean()
        osoba = cleaned_data.get("osoba")
        data_form = cleaned_data.get("data_pochowania")

        if osoba:
            # Sprawdza akt zgonu
            zgon_db = Zgon.objects.filter(osoba=osoba).first()

            # Jeśli w formularzu PUSTO, a w bazie JEST -> Pobierz z bazy
            if not data_form:
                if zgon_db and zgon_db.data_pogrzebu:
                    cleaned_data['data_pochowania'] = zgon_db.data_pogrzebu
                else:
                    self.add_error('data_pochowania', "Brak daty w Akcie Zgonu. Musisz wpisać datę ręcznie.")
            
        return cleaned_data

    def save(self, commit=True):
        pochowany = super().save(commit=False)
        
        if commit:
            pochowany.save()
            
            # --- 3. AUTOMATYZACJA: AKT ZGONU ---
            osoba = pochowany.osoba
            data = pochowany.data_pochowania
            grob_opis = f"{pochowany.grob.sektor} / {pochowany.grob.numer}"
            
            # Pobieramy lub tworzymy
            zgon = Zgon.objects.filter(osoba=osoba).first()
            
            if not zgon:
                # Tworzymy nowy akt, jeśli nie istnieje
                rok_biezacy = data.year if data else timezone.now().year
                zgon = Zgon(
                    osoba=osoba,
                    rok=str(rok_biezacy), # Wstępny rok
                    akt_nr="roboczy"      # Tymczasowy numer
                )
            
            # Aktualizujemy dane
            if data:
                zgon.data_pogrzebu = data
                zgon.data_zgonu = data 
            
            # Dopisujemy miejsce
            if zgon.cmentarz:
                if grob_opis not in zgon.cmentarz:
                    zgon.cmentarz = f"{zgon.cmentarz}, {grob_opis}"
            else:
                zgon.cmentarz = f"Parafialny, {grob_opis}"
                
            zgon.save()

        return pochowany