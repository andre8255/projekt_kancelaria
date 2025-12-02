# sakramenty/forms.py
from django.utils import timezone
from django import forms
from django.db import transaction   
from .models import Chrzest, PierwszaKomunia, Bierzmowanie, Malzenstwo, NamaszczenieChorych, Zgon
from osoby.models import Osoba
from slowniki.models import Parafia, Duchowny 
from django.db.models import Q, Max


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

class DateInput(forms.DateInput):
    input_type = "date"

# =============================================================================
# === SPECJALNE POLE LISTY (Z DATĄ URODZENIA) ===
# =============================================================================
class OsobaChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Etykieta: "Kowalski Jan (ur. 1990-01-01, s. Adama)"
        opis = f"{obj.nazwisko} {obj.imie_pierwsze}"
        szczegoly = []
        
        if obj.data_urodzenia:
            szczegoly.append(f"ur. {obj.data_urodzenia}")
             
        if szczegoly:
            opis += f" ({', '.join(szczegoly)})"
        return opis

# =============================================================================
# === POMOCNICZA FUNKCJA WALIDACJI NUMERACJI ===
# =============================================================================
def ustal_numer_aktu(model_class, rok, podany_nr, instance_pk=None):
    """
    Zwraca: (czy_sukces, wynik_lub_blad)
    """
    if not rok:
        return False, "Brak roku - nie można zweryfikować numeru aktu."

    if podany_nr:
        # A) RĘCZNY: Sprawdzamy czy numer nie jest zajęty
        # Opcjonalnie: sprawdzamy czy to cyfra (jeśli wymagasz tylko cyfr)
        # if not str(podany_nr).isdigit():
        #      return False, "Numer aktu może składać się tylko z cyfr."
        
        qs = model_class.objects.filter(rok=rok, akt_nr=podany_nr)
        if instance_pk:
            qs = qs.exclude(pk=instance_pk)
        
        if qs.exists():
            return False, f"Numer aktu {podany_nr} w roku {rok} już istnieje! Wybierz inny."
        
        return True, podany_nr
    else:
        # B) AUTOMAT: Szukamy najwyższego numeru i dodajemy 1
        istniejace = model_class.objects.filter(rok=rok).values_list('akt_nr', flat=True)
        max_nr = 0
        for numer_str in istniejace:
            if numer_str and numer_str.isdigit():
                n = int(numer_str)
                if n > max_nr:
                    max_nr = n
        return True, str(max_nr + 1)


# =============================================================================
# === CHRZEST FORMULARZ ===
# =============================================================================
class ChrzestForm(BootstrapFormMixin, forms.ModelForm):
    ochrzczony = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by('nazwisko', 'imie_pierwsze'),
        label="Osoba ochrzczona",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = Chrzest
        fields = [
            "rok", "akt_nr", "ochrzczony",
            "data_urodzenia", "rok_urodzenia", "miejsce_urodzenia",
            "data_chrztu", "rok_chrztu", "miejsce_chrztu", "parafia",
            "ojciec", "ojciec_wyznanie",
            "matka", "nazwisko_matki_rodowe", "matka_wyznanie",
            "uwagi_wew", "skan_aktu",
        ]
        widgets = {
            "data_urodzenia": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "data_chrztu": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "uwagi_wew": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if "ochrzczony" in self.fields:
            css = self.fields["ochrzczony"].widget.attrs.get("class", "")
            self.fields["ochrzczony"].widget.attrs["class"] = (css + " js-osoba-select").strip()


        # Ukrywamy pole osoby, jeśli jest już ustawiona (np. przy dodawaniu z profilu)
        if self.initial.get("ochrzczony") and not self.instance.pk:
            self.fields["ochrzczony"].widget = forms.HiddenInput()

        # Formaty dat
        self.fields["data_urodzenia"].input_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"]
        self.fields["data_chrztu"].input_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"]
        
        # Pola "Rok" i "Nr aktu" nie są wymagane w HTML (bo automat je wypełni)
        self.fields["rok"].required = False
        self.fields["rok"].widget.attrs.pop("required", None)
        self.fields["rok"].widget.attrs["placeholder"] = "Auto"
        
        self.fields["akt_nr"].required = False
        self.fields["akt_nr"].widget.attrs.pop("required", None)
        self.fields["akt_nr"].widget.attrs["placeholder"] = "Auto"

        if "rok_chrztu" in self.fields:
            self.fields["rok_chrztu"].required = False

    def clean(self):
        cleaned_data = super().clean()
        today = timezone.localdate()
        parafia = cleaned_data.get("parafia")

        if not parafia:
            self.add_error("parafia", "Musisz wybrać parafię, w której odbył się chrzest.")
        # 1. Walidacja duplikatu osoby
        osoba = cleaned_data.get("ochrzczony")
        if osoba:
            qs = Chrzest.objects.filter(ochrzczony=osoba)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("ochrzczony", "Ta osoba ma już wpis chrztu.")

        # 2. Automatyczne ustalanie ROKU KSIĘGI
        rok_ksiegi = cleaned_data.get("rok")
        data_chrztu = cleaned_data.get("data_chrztu")
        rok_chrztu = cleaned_data.get("rok_chrztu")

        # Zmienna pomocnicza na ostateczny rok
        finalny_rok = rok_ksiegi

        if not finalny_rok:
            if data_chrztu:
                finalny_rok = data_chrztu.year
                cleaned_data["rok"] = finalny_rok
            elif rok_chrztu:
                finalny_rok = rok_chrztu
                cleaned_data["rok"] = finalny_rok
            else:
                self.add_error("rok", "Musisz podać Datę chrztu, Rok chrztu lub wpisać Rok księgi ręcznie.")
                # Przerywamy, bo bez roku nie ustalimy numeru
                return cleaned_data

        # 3. Walidacja / Automat NUMERU AKTU
        # Korzystamy z funkcji pomocniczej zdefiniowanej wyżej
        akt_nr = cleaned_data.get("akt_nr")
        
        # Wywołanie: (Model, rok, nr_reczny, id_do_wykluczenia)
        sukces, wynik = ustal_numer_aktu(Chrzest, finalny_rok, akt_nr, self.instance.pk)
        
        if sukces:
            # Jeśli sukces, 'wynik' to poprawny numer (ręczny lub automatyczny)
            cleaned_data["akt_nr"] = wynik
        else:
            # Jeśli błąd, 'wynik' to treść komunikatu błędu
            self.add_error("akt_nr", wynik)

        # 4. Walidacja dat
        data_urodzenia = cleaned_data.get("data_urodzenia")
        if data_chrztu:
            if data_chrztu > today:
                self.add_error("data_chrztu", "Data chrztu nie może być z przyszłości.")
            
            if data_urodzenia and data_chrztu < data_urodzenia:
                self.add_error("data_chrztu", "Data chrztu nie może być wcześniejsza niż data urodzenia.")

        return cleaned_data


# =============================================================================
# === I KOMUNIA ŚWIĘTA (ZMODYFIKOWANA)
# =============================================================================
class PierwszaKomuniaForm(BootstrapFormMixin, forms.ModelForm):
    # ZMIANA: Ulepszone pole wyboru
    osoba = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by('nazwisko', 'imie_pierwsze'),
        label="Osoba",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = PierwszaKomunia
        fields = ["osoba", "rok", "parafia", "uwagi_wew"]
        widgets = {
            "uwagi_wew": forms.Textarea(attrs={"rows": 3}),
            # ZMIANA: TextInput z blokadą wpisywania
            "rok": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "RRRR",
                "maxlength": "4",  # Blokuje wpisanie więcej niż 4 znaków
                # Skrypt JS blokujący wpisywanie liter (pozwala tylko na cyfry)
                "oninput": "this.value = this.value.replace(/[^0-9]/g, '');"
            }),
        }
        labels = {
            "rok": "Rok I Komunii",
            "parafia": "Parafia (miejsce Komunii)",
            "uwagi_wew": "Uwagi (tylko do kancelarii)",
        }
            
    def clean_rok(self):
        rok = self.cleaned_data.get("rok")
        if rok:
            # Dodatkowa weryfikacja po stronie serwera
            if not str(rok).isdigit() or len(str(rok)) != 4:
                raise forms.ValidationError("Rok musi składać się dokładnie z 4 cyfr.")
            
            current_year = timezone.now().year
            if int(rok) > current_year + 1:
                 raise forms.ValidationError("Rok nie może być z dalekiej przyszłości.")
        return rok

    def clean(self):
        cleaned = super().clean()
        parafia = cleaned.get("parafia")
        if not parafia:
            self.add_error("parafia", "Musisz wybrać parafię I Komunii.")
        osoba = cleaned.get("osoba")
        if osoba:
            qs = PierwszaKomunia.objects.filter(osoba=osoba)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Ta osoba ma już wpis I Komunii Świętej.")
        return cleaned
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # to pole, na którym chcesz mieć „live search”
        if "osoba" in self.fields:
            css = self.fields["osoba"].widget.attrs.get("class", "")
            self.fields["osoba"].widget.attrs["class"] = (css + " js-osoba-select").strip()

# =============================================================================
# === BIERZMOWANIE
# =============================================================================
class BierzmowanieForm(BootstrapFormMixin, forms.ModelForm):
    osoba = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by('nazwisko', 'imie_pierwsze'),
        label="Kandydat do bierzmowania",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    szafarz = forms.ModelChoiceField(
        queryset=Duchowny.objects.filter(aktywny=True).order_by("imie_nazwisko"),
        required=False, label="Szafarz (Biskup)", empty_label="--- wybierz ---"
    )
    parafia_nowa = forms.CharField(required=False, label="Albo wpisz nową parafię", widget=forms.TextInput(attrs={"class": "form-control"}))
    szafarz_nowy = forms.CharField(required=False, label="Albo wpisz nowego szafarza", widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = Bierzmowanie
        fields = ["osoba", "rok", "akt_nr", "data_bierzmowania", "miejsce_bierzmowania", "imie_bierzmowania", "parafia", "szafarz", "swiadek", "uwagi_wew", "skan_aktu"]
        widgets = {
            "osoba": forms.Select(attrs={"class": "form-control"}),
            "rok": forms.TextInput(attrs={"class": "form-control", "placeholder": "Rok"}),
            "akt_nr": forms.TextInput(attrs={"class": "form-control", "placeholder": "Auto"}),
            "data_bierzmowania": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "uwagi_wew": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if "osoba" in self.fields:
            css = self.fields["osoba"].widget.attrs.get("class", "")
            self.fields["osoba"].widget.attrs["class"] = (css + " js-osoba-select").strip()


        # Rok jako Select
        biezacy_rok = timezone.now().year
        ZAKRES_LAT = range(biezacy_rok - 100, biezacy_rok + 6)
        wybory_lat = [('', '---------')] + [(r, r) for r in reversed(ZAKRES_LAT)]
        self.fields['rok'].widget = forms.Select(choices=wybory_lat, attrs={'class': 'form-select form-select-sm'})

        self.fields["rok"].required = False
        self.fields["akt_nr"].required = False
        self.fields["parafia"].required = False
        self.fields["szafarz"].required = False

    def clean(self):
        cleaned = super().clean()

        # --- WALIDACJA PARAFII (Lista LUB Ręczna) ---
        parafia = cleaned.get("parafia")
        parafia_reczna = cleaned.get("parafia_nazwa_reczna")
        
        if not parafia and not parafia_reczna:
             msg = "Wybierz parafię z listy LUB wpisz nazwę ręcznie."
             self.add_error("parafia", msg)
             self.add_error("parafia_nazwa_reczna", msg)

        today = timezone.localdate()
        osoba = cleaned.get("osoba")
        if osoba:
            qs = Bierzmowanie.objects.filter(osoba=osoba)
            if self.instance.pk: qs = qs.exclude(pk=self.instance.pk)
            if qs.exists(): raise forms.ValidationError("Ta osoba ma już wpis bierzmowania.")

        data_bierzmowania = cleaned.get("data_bierzmowania")
        rok = cleaned.get("rok")
        if not rok and data_bierzmowania:
            rok = data_bierzmowania.year
            cleaned["rok"] = rok

        akt_nr = cleaned.get("akt_nr")
        if rok:
            sukces, wynik = ustal_numer_aktu(Bierzmowanie, rok, akt_nr, self.instance.pk)
            if sukces: cleaned["akt_nr"] = wynik
            else: self.add_error("akt_nr", wynik)
        else:
            if not akt_nr: self.add_error("rok", "Podaj datę bierzmowania lub rok.")

        if data_bierzmowania:
            if data_bierzmowania > today: self.add_error("data_bierzmowania", "Data z przyszłości.")
            if not osoba and self.instance.pk: osoba = self.instance.osoba
            if osoba and getattr(osoba, 'data_urodzenia', None):
                if data_bierzmowania < osoba.data_urodzenia:
                    self.add_error('data_bierzmowania', 'Data bierzmowania wcześniejsza niż urodzenie.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        c = self.cleaned_data
        if c.get("rok") is not None: instance.rok = c["rok"]
        
        if c.get("parafia"):
             instance.parafia = c["parafia"]
             if hasattr(instance, "parafia_nazwa_reczna"): instance.parafia_nazwa_reczna = ""
        else:
             instance.parafia = None
             if hasattr(instance, "parafia_nazwa_reczna"): instance.parafia_nazwa_reczna = (c.get("parafia_nowa") or "").strip()
        
        if c.get("szafarz"):
             instance.szafarz = c["szafarz"]
             if hasattr(instance, "szafarz_opis_reczny"): instance.szafarz_opis_reczny = ""
        else:
             instance.szafarz = None
             if hasattr(instance, "szafarz_opis_reczny"): instance.szafarz_opis_reczny = (c.get("szafarz_nowy") or "").strip()
        if commit: instance.save()
        return instance


# =============================================================================
# === MAŁŻEŃSTWO
# =============================================================================
class MalzenstwoForm(BootstrapFormMixin, forms.ModelForm):
    # ZMIANA: Ulepszone pola wyboru dla obu małżonków
    malzonek_a = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by('nazwisko'),
        label="Małżonek A (Mąż)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    malzonek_b = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by('nazwisko'),
        label="Małżonek B (Żona)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    swiadek_urzedowy = forms.ModelChoiceField(
        queryset=Duchowny.objects.filter(aktywny=True),
        required=False, label="Duchowny asystujący", empty_label="--- wybierz ---"
    )

    malzonek_b = forms.ModelChoiceField(queryset=Osoba.objects.all().order_by("nazwisko", "imie_pierwsze"), label="Współmałżonek")
    parafia = forms.ModelChoiceField(queryset=Parafia.objects.all().order_by("nazwa"), required=False)
    parafia_opis_reczny = forms.CharField(required=False, widget=forms.TextInput())
    swiadek_urzedowy = forms.ModelChoiceField(queryset=Duchowny.objects.all().order_by("tytul", "imie_nazwisko"), required=False)
    swiadek_urzedowy_opis_reczny = forms.CharField(required=False, widget=forms.TextInput())

    class Meta:
        model = Malzenstwo
        fields = ["malzonek_a", "malzonek_b", "rok", "akt_nr", "data_slubu", "parafia", "parafia_opis_reczny", "swiadek_urzedowy", "swiadek_urzedowy_opis_reczny", "swiadek_a", "swiadek_b", "uwagi_wew", "skan_aktu"]
        widgets = {
            "rok": forms.TextInput(attrs={"placeholder": "Rok"}),
            "akt_nr": forms.TextInput(attrs={"placeholder": "Auto"}),
            "data_slubu": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "uwagi_wew": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.fixed_malzonek_a = kwargs.pop("malzonek_a_obj", None)
        super().__init__(*args, **kwargs)
        biezacy_rok = timezone.now().year
        ZAKRES_LAT = range(biezacy_rok - 100, biezacy_rok + 6)
        wybory_lat = [('', '---------')] + [(r, r) for r in reversed(ZAKRES_LAT)]
        self.fields['rok'].widget = forms.Select(choices=wybory_lat, attrs={'class': 'form-select form-select-sm'})
        self.fields["rok"].required = False
        self.fields["akt_nr"].required = False
        self.fields["malzonek_a"].queryset = Osoba.objects.order_by("nazwisko","imie_pierwsze")
        self.fields["malzonek_b"].queryset = Osoba.objects.order_by("nazwisko","imie_pierwsze")
        if self.fixed_malzonek_a: self.fields["malzonek_a"].required = False

        if "osoba" in self.fields:
            css = self.fields["osoba"].widget.attrs.get("class", "")
            self.fields["osoba"].widget.attrs["class"] = (css + " js-osoba-select").strip()

    def clean(self):
        cleaned = super().clean()

        parafia = cleaned.get("parafia")
        parafia_reczna = cleaned.get("parafia_opis_reczny")
        
        if not parafia and not parafia_reczna:
             msg = "Wybierz parafię ślubu z listy LUB wpisz nazwę ręcznie."
             self.add_error("parafia", msg)
             self.add_error("parafia_opis_reczny", msg)
        
        mA = cleaned.get("malzonek_a")
        mB = cleaned.get("malzonek_b")
        if mA and mB and mA == mB:
            self.add_error("malzonek_b", "Małżonkowie muszą być różnymi osobami.")

        data_slubu = cleaned.get("data_slubu")
        rok = cleaned.get("rok")
        if not rok and data_slubu:
            rok = data_slubu.year
            cleaned["rok"] = rok

        akt_nr = cleaned.get("akt_nr")
        if rok:
            sukces, wynik = ustal_numer_aktu(Malzenstwo, rok, akt_nr, self.instance.pk)
            if sukces: cleaned["akt_nr"] = wynik
            else: self.add_error("akt_nr", wynik)
        else:
            if not akt_nr: self.add_error("rok", "Podaj datę ślubu lub rok.")

        a = cleaned.get("malzonek_a") or self.fixed_malzonek_a or self.initial.get("malzonek_a") or self.instance.malzonek_a
        b = cleaned.get("malzonek_b")
        if a and not hasattr(a, "pk"): a = Osoba.objects.filter(pk=a).first()
        if not a: self.add_error("malzonek_a", "Wskaż małżonka A.")
        if not b: self.add_error("malzonek_b", "Wskaż małżonka B.")
        if a and b and a == b: self.add_error("malzonek_b", "Małżonkowie muszą być różni.")
        return cleaned


# =============================================================================
# === NAMASZCZENIE CHORYCH
# =============================================================================
class NamaszczenieChorychForm(BootstrapFormMixin, forms.ModelForm):
    # ZMIANA: Ulepszone pole wyboru
    osoba = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by('nazwisko'),
        label="Chory / Osoba",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    szafarz = forms.ModelChoiceField(
        queryset=Duchowny.objects.filter(aktywny=True),
        required=False, empty_label="--- wybierz ---"
    )

    MIEJSCE_CHOICES = [
        ("Dom chorego", "Dom chorego"),
        ("Szpital", "Szpital"),
        ("Kościół", "Kościół"),
        ("Inne", "Inne"),
    ]

    miejsce = forms.ChoiceField(
    choices=MIEJSCE_CHOICES,
    label="Miejsce posługi",
    widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = NamaszczenieChorych
        fields = [
            "osoba",
            "data",
            "miejsce",
            "szafarz",
            "spowiedz",
            "komunia",
            "namaszczenie",
            "uwagi_wew",
        ]
    class Meta:
        model = NamaszczenieChorych
        fields = ["osoba", "data", "miejsce", "szafarz", "spowiedz", "komunia", "namaszczenie", "uwagi_wew"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "uwagi_wew": forms.Textarea(attrs={"rows": 3}),
        }
    def clean(self):
        cleaned = super().clean()
        today = timezone.localdate()
        if not self.initial.get("osoba") and not cleaned.get("osoba"): self.add_error("osoba", "Wybierz osobę.")
        data = cleaned.get("data")
        if data:
            if data > today: self.add_error("data", "Data z przyszłości.")
            osoba = cleaned.get("osoba")
            if not osoba and self.instance.pk: osoba = self.instance.osoba
            if osoba and getattr(osoba, 'data_urodzenia', None):
                if data < osoba.data_urodzenia: self.add_error("data", "Data wcześniejsza niż urodzenie.")
        return cleaned
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # to pole, na którym chcesz mieć „live search”
        if "osoba" in self.fields:
            css = self.fields["osoba"].widget.attrs.get("class", "")
            self.fields["osoba"].widget.attrs["class"] = (css + " js-osoba-select").strip()

# =============================================================================
# === ZGON
# =============================================================================
class ZgonForm(BootstrapFormMixin, forms.ModelForm):
    # ZMIANA: Ulepszone pole wyboru
    osoba = OsobaChoiceField(
        queryset=Osoba.objects.all().order_by('nazwisko'),
        label="Osoba zmarła",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Zgon
        fields = [
            "osoba",
            "rok",
            "akt_nr",
            "data_zgonu",
            "miejsce_zgonu",
            "data_pogrzebu",
            "cmentarz",
            "uwagi_wew",
            "skan_aktu"
        ]
        widgets = {
            "data_zgonu": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "data_pogrzebu": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "uwagi_wew": forms.Textarea(attrs={"rows":3}),
            "akt_nr": forms.TextInput(attrs={"placeholder": "Auto"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "osoba" in self.fields:
            css = self.fields["osoba"].widget.attrs.get("class", "")
            self.fields["osoba"].widget.attrs["class"] = (css + " js-osoba-select").strip()
        self.fields["osoba"].queryset = Osoba.objects.order_by("nazwisko", "imie_pierwsze")
        self.fields["osoba"].label = "Osoba zmarła"
        
        # Pola opcjonalne (dla automatu)
        self.fields["rok"].required = False
        self.fields["akt_nr"].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        # Pobieramy dane
        data_zgonu = cleaned_data.get("data_zgonu")
        rok = cleaned_data.get("rok")
        akt_nr = cleaned_data.get("akt_nr")

        # 1. Walidacja spójności ROKU
        # Jeśli podano rok I datę zgonu, muszą się one zgadzać
        if rok and data_zgonu:
            # rzutujemy na int dla pewności (rok może przyjść jako string z formularza)
            if int(rok) != data_zgonu.year:
                self.add_error(
                    "rok", 
                    f"Rok aktu ({rok}) musi być zgodny z datą zgonu ({data_zgonu.year})."
                )
                # Możesz też dodać błąd do daty, jeśli wolisz:
                # self.add_error("data_zgonu", "Data zgonu nie pasuje do roku aktu.")

        # 2. AUTO-ROK (jeśli rok pusty)
        if (rok is None or str(rok).strip() == "") and data_zgonu:
            rok = data_zgonu.year
            cleaned_data["rok"] = rok

        # 3. Numeracja (Automat)
        if rok:
            # Sprawdzamy unikalność / generujemy numer TYLKO jeśli rok jest poprawny (zgodny z datą)
            # Jeśli wyżej był błąd walidacji roku, to i tak formularz nie przejdzie, 
            # ale warto tu sprawdzić czy 'rok' nie jest błędny.
            if not self.has_error('rok'): 
                sukces, wynik = ustal_numer_aktu(Zgon, rok, akt_nr, self.instance.pk)
                if sukces:
                    cleaned_data["akt_nr"] = wynik
                else:
                    self.add_error("akt_nr", wynik)
        else:
            if not akt_nr:
                self.add_error("rok", "Podaj datę zgonu lub rok.")

        # 4. Walidacja Nr Aktu (format)
        if akt_nr and not str(akt_nr).isdigit():
             self.add_error("akt_nr", "Numer aktu może składać się tylko z cyfr.")

        # 5. Walidacje dat (chronologia)
        osoba = cleaned_data.get("osoba") 
        if not osoba and self.instance.pk:
            osoba = self.instance.osoba
        
        if not osoba:
            return cleaned_data

        data_urodzenia = getattr(osoba, 'data_urodzenia', None)
        data_pogrzebu = cleaned_data.get("data_pogrzebu")
        today = timezone.localdate()

        if data_zgonu:
            if data_zgonu > today:
                self.add_error('data_zgonu', 'Data zgonu nie może być z przyszłości.')
            
            if data_urodzenia and data_zgonu < data_urodzenia:
                self.add_error('data_zgonu', 'Data zgonu nie może być wcześniejsza niż data urodzenia.')

        if data_zgonu and data_pogrzebu:
            if data_pogrzebu < data_zgonu:
                self.add_error('data_pogrzebu', 'Data pogrzebu nie może być wcześniejsza niż data zgonu.')

        return cleaned_data

    def save(self, commit=True):
        """
        Nadpisujemy save, aby upewnić się, że wyliczony w clean() rok i numer
        trafią do obiektu (instancji), nawet jeśli pola w formularzu były puste.
        """
        instance = super().save(commit=False)
        
        # Przypisujemy wartości z cleaned_data (tam jest nasz wyliczony rok i numer)
        if self.cleaned_data.get("rok"):
            instance.rok = self.cleaned_data["rok"]
        
        if self.cleaned_data.get("akt_nr"):
            instance.akt_nr = self.cleaned_data["akt_nr"]

        if commit:
            instance.save()
        return instance