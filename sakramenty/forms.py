#sakramenty/forms.py
from django import forms
from django.db import transaction   
from .models import Chrzest, PierwszaKomunia,Bierzmowanie,Malzenstwo,NamaszczenieChorych,Zgon
from osoby.models import Osoba
from slowniki.models import Parafia, Duchowny 
from django.db.models import Q

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

class ChrzestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Chrzest
        fields = [
            "rok", "akt_nr",
            "ochrzczony",                 # <— tu wracamy do ochrzczony
            "data_urodzenia", "rok_urodzenia", "miejsce_urodzenia",
            "data_chrztu", "rok_chrztu", "miejsce_chrztu",
            "ojciec", "ojciec_wyznanie",
            "matka", "nazwisko_matki_rodowe", "matka_wyznanie",
            "uwagi_wew",
        ]
        widgets = {
            "data_urodzenia": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "data_chrztu":    forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "uwagi_wew": forms.Textarea(attrs={"rows":3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # jeśli przyszliśmy z profilu osoby (initial zawiera ochrzczony) – schowaj to pole
        if self.initial.get("ochrzczony") and not self.instance.pk:
            self.fields["ochrzczony"].widget = forms.HiddenInput()

        self.fields["data_urodzenia"].input_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"]
        self.fields["data_chrztu"].input_formats    = ["%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"]
        self.fields["ojciec"].widget.attrs.setdefault("placeholder", "wpisz imię i nazwisko")
        self.fields["matka"].widget.attrs.setdefault("placeholder", "wpisz imię i nazwisko")
        self.fields["nazwisko_matki_rodowe"].widget.attrs.setdefault("placeholder", "np. Kowalska")
        # >>> TU: pola nieobowiązkowe, żeby nie pojawiało się „Wypełnij to pole”
        self.fields["rok"].required = False
        self.fields["rok"].widget.attrs.pop("required", None)

        if "rok_chrztu" in self.fields:
            self.fields["rok_chrztu"].required = False
            self.fields["rok_chrztu"].widget.attrs.pop("required", None)
    def clean(self):
        cleaned = super().clean()

        # duplikat chrztu dla tej osoby
        osoba = cleaned.get("ochrzczony")
        if osoba:
            qs = Chrzest.objects.filter(ochrzczony=osoba)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Ta osoba ma już wpis chrztu.")

        # AUTO: rok i/lub rok_chrztu z daty chrztu
        data_chrztu = cleaned.get("data_chrztu")
        rok_ksiegi = cleaned.get("rok")
        rok_chrztu = cleaned.get("rok_chrztu")

        if data_chrztu:
            if not rok_ksiegi:
                cleaned["rok"] = data_chrztu.year
            if "rok_chrztu" in self.fields and not rok_chrztu:
                cleaned["rok_chrztu"] = data_chrztu.year

        # Spójność: data chrztu nie wcześniej niż data urodzenia
        data_urodzenia = cleaned.get("data_urodzenia")
        if data_chrztu and data_urodzenia and data_chrztu < data_urodzenia:
            self.add_error("data_chrztu", "Data chrztu nie może być wcześniejsza niż data urodzenia.")

        return cleaned




class PierwszaKomuniaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = PierwszaKomunia
        fields = ["osoba","rok", "parafia", "uwagi_wew"]

        widgets = {
            "uwagi_wew": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "rok": "Rok I Komunii",
            "parafia": "Parafia (miejsce Komunii)",
            "uwagi_wew": "Uwagi (tylko do kancelarii)",
        }
        help_texts = {
            "rok": "Np. 1998. Możesz wpisać tylko rok.",
            "parafia": "Np. Parafia św. Leonarda Opata w Mykanowie",
        }
    def clean(self):
        cleaned = super().clean()
        osoba = cleaned.get("osoba")
        if osoba:
            qs = PierwszaKomunia.objects.filter(osoba=osoba)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Ta osoba ma już wpis I Komunii Świętej.")
        return cleaned


class BierzmowanieForm(forms.ModelForm):
    parafia_nowa = forms.CharField(
        required=False,
        label="Albo wpisz nową parafię",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Jeśli nie ma na liście powyżej, wpisz ręcznie."
    )
    szafarz_nowy = forms.CharField(
        required=False,
        label="Albo wpisz nowego szafarza",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Np. «bp Jan Kowalski» albo «ks. Piotr Nowak»"
        }),
        help_text="Jeśli brak na liście powyżej, wpisz ręcznie."
    )

    class Meta:
        model = Bierzmowanie
        fields = [
            "osoba",
            "rok",
            "akt_nr",
            "data_bierzmowania",
            "miejsce_bierzmowania",
            "imie_bierzmowania",
            "parafia",
            "szafarz",
            "swiadek",
            "uwagi_wew",
        ]
        widgets = {
            "osoba": forms.Select(attrs={"class": "form-control"}),
            "rok": forms.TextInput(attrs={"class": "form-control", "placeholder": "Rok bierzmowania"}),
            "akt_nr": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nr aktu bierzmowania"}),
            "data_bierzmowania": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "imie_bierzmowania": forms.TextInput(attrs={"class": "form-control"}),
            "miejsce_bierzmowania": forms.TextInput(attrs={"class": "form-control"}),
            "parafia": forms.Select(attrs={"class": "form-control"}),
            "szafarz": forms.Select(attrs={"class": "form-control"}),
            "swiadek": forms.TextInput(attrs={"class": "form-control"}),
            "uwagi_wew": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rok ma być opcjonalny (uzupełnimy z daty)
        self.fields["rok"].required = False
        self.fields["rok"].widget.attrs.pop("required", None)
        # Te też mogą być puste
        self.fields["parafia"].required = False
        self.fields["szafarz"].required = False

    def clean(self):
        cleaned = super().clean()

        # Unikalność – jedna pozycja bierzmowania na osobę
        osoba = cleaned.get("osoba")
        if osoba:
            qs = Bierzmowanie.objects.filter(osoba=osoba)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Ta osoba ma już wpis bierzmowania.")

        # Auto: rok z daty
        data_bierzmowania = cleaned.get("data_bierzmowania")
        rok = cleaned.get("rok")

        if (rok is None or str(rok).strip() == "") and data_bierzmowania:
            cleaned["rok"] = data_bierzmowania.year  # <- int dla (Positive)IntegerField

        # (opcjonalnie) jeśli chcesz wymagać chociaż rok lub datę:
        # if not cleaned.get("rok") and not data_bierzmowania:
        #     self.add_error("rok", "Podaj rok bierzmowania lub pełną datę bierzmowania.")

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        c = self.cleaned_data

        # Rok już ustawiony w clean(); nic tu nie wyliczamy
        if c.get("rok") is not None:
            instance.rok = c["rok"]

        # Parafia: albo wybrana, albo tekst
        wybrana_parafia = c.get("parafia")
        nowa_parafia_txt = (c.get("parafia_nowa") or "").strip()
        if wybrana_parafia:
            instance.parafia = wybrana_parafia
            if hasattr(instance, "parafia_nazwa_reczna"):
                instance.parafia_nazwa_reczna = ""
        else:
            instance.parafia = None
            if hasattr(instance, "parafia_nazwa_reczna"):
                instance.parafia_nazwa_reczna = nowa_parafia_txt

        # Szafarz: albo wybrany, albo tekst
        wybrany_szafarz = c.get("szafarz")
        nowy_szafarz_txt = (c.get("szafarz_nowy") or "").strip()
        if wybrany_szafarz:
            instance.szafarz = wybrany_szafarz
            if hasattr(instance, "szafarz_opis_reczny"):
                instance.szafarz_opis_reczny = ""
        else:
            instance.szafarz = None
            if hasattr(instance, "szafarz_opis_reczny"):
                instance.szafarz_opis_reczny = nowy_szafarz_txt

        if commit:
            instance.save()
        return instance

#-------------Małżeństwo------------
class MalzenstwoForm(BootstrapFormMixin, forms.ModelForm):
    # to wybieramy osobę B (drugi małżonek)
    malzonek_b = forms.ModelChoiceField(
        queryset=Osoba.objects.all().order_by("nazwisko", "imie_pierwsze"),
        label="Współmałżonek",
        help_text="Wybierz osobę, z którą zawarto małżeństwo."
    )

    # parafia - wybór z listy
    parafia = forms.ModelChoiceField(
        queryset=Parafia.objects.all().order_by("nazwa"),
        required=False,
        label="Parafia ślubu",
        help_text="Wybierz z listy, albo wpisz nową parafię poniżej (ręcznie)."
    )

    # parafia wpisana ręcznie
    parafia_opis_reczny = forms.CharField(
        required=False,
        label="Albo wpisz nową parafię",
        help_text="Jeśli nie ma na liście powyżej.",
        widget=forms.TextInput()
    )

    # świadek urzędowy / asystujący – wybór duchownego
    swiadek_urzedowy = forms.ModelChoiceField(
        queryset=Duchowny.objects.all().order_by("tytul", "imie_nazwisko"),
        required=False,
        label="Świadek urzędowy / asystujący",
        help_text="Kapłan / diakon, który asystował przy zawarciu małżeństwa."
    )

    # świadek wpisany ręcznie
    swiadek_urzedowy_opis_reczny = forms.CharField(
        required=False,
        label="Albo wpisz nowego świadka/asystującego",
        help_text="Np. «ks. Jan Kowalski», jeśli nie ma go na liście powyżej.",
        widget=forms.TextInput()
    )

    class Meta:
        model = Malzenstwo
        fields = [
            "malzonek_a",
            "malzonek_b",

            "rok",
            "akt_nr",
            "data_slubu",

            "parafia",
            "parafia_opis_reczny",

            "swiadek_urzedowy",
            "swiadek_urzedowy_opis_reczny",

            "uwagi_wew",
        ]
        widgets = {
            "rok": forms.TextInput(attrs={"placeholder": "Rok ślubu"}),
            "akt_nr": forms.TextInput(attrs={"placeholder": "Nr aktu małżeństwa"}),
            "data_slubu": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d"
            ),
            "uwagi_wew": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        # przyjmij obiekt małżonka A, jeśli przyszedł z widoku
        self.fixed_malzonek_a = kwargs.pop("malzonek_a_obj", None)
        super().__init__(*args, **kwargs)
        
        self.fields["rok"].required = False
        self.fields["rok"].widget.attrs.pop("required", None)
        # ładne kolejności do wyboru
        self.fields["malzonek_a"].queryset = Osoba.objects.order_by("nazwisko","imie_pierwsze")
        self.fields["malzonek_b"].queryset = Osoba.objects.order_by("nazwisko","imie_pierwsze")
    
        # gdy dodajemy z profilu osoby – pole może być ukryte (ale nie musi)
        if self.fixed_malzonek_a:
            # nie wymagaj wartości z POST, bo i tak ustawimy ją w widoku
            self.fields["malzonek_a"].required = False



    def clean(self):
        cleaned = super().clean()

        # auto-rok z daty ślubu
        data_slubu = cleaned.get("data_slubu")
        rok = cleaned.get("rok")
        if (rok is None or str(rok).strip() == "") and data_slubu:
            cleaned["rok"] = data_slubu.year  # int dla (Positive)IntegerField

        # walidacje małżonków (Twoje dotychczasowe)
        a = cleaned.get("malzonek_a") or self.fixed_malzonek_a or self.initial.get("malzonek_a") or self.instance.malzonek_a
        b = cleaned.get("malzonek_b")
        if a and not hasattr(a, "pk"):
            a = Osoba.objects.filter(pk=a).first()
        if not a:
            self.add_error("malzonek_a", "Wskaż małżonka A.")
        if not b:
            self.add_error("malzonek_b", "Wskaż małżonka B.")
        if a and b and a == b:
            self.add_error("malzonek_b", "Małżonkowie muszą być różni.")

        return cleaned

#----------Namaszczenie chorych------------
class NamaszczenieChorychForm(BootstrapFormMixin, forms.ModelForm):
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
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "uwagi_wew": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "data": "Data posługi",
            "miejsce": "Miejsce",
            "szafarz": "Szafarz",
            "spowiedz": "Spowiedź",
            "komunia": "Komunia Święta",
            "namaszczenie": "Namaszczenie chorych",
            "uwagi_wew": "Uwagi duszpasterskie",
        }
        help_texts = {
            "miejsce": "Np. dom chorego, szpital",
            "szafarz": "Kto udzielił posługi (np. ks. Jan Nowak)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Gdy wchodzimy z profilu osoby (initial['osoba'] ustawione w widoku) – schowaj pole
       

    def clean(self):
        cleaned = super().clean()
        # Dodatkowy bezpiecznik: z listy osoba musi być wskazana
        if not self.initial.get("osoba") and not cleaned.get("osoba"):
            self.add_error("osoba", "Wybierz osobę.")
        return cleaned
    
#------------Zgon----------------------
class ZgonForm(BootstrapFormMixin, forms.ModelForm):
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
        ]
        widgets = {
            "data_zgonu": forms.DateInput(attrs={"type": "date"}),
            "data_pogrzebu": forms.DateInput(attrs={"type": "date"}),
            "uwagi_wew": forms.Textarea(attrs={"rows":3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # lista osób uporządkowana alfabetycznie do wyboru zmarłego
        self.fields["osoba"].queryset = Osoba.objects.order_by("nazwisko", "imie_pierwsze")
        self.fields["osoba"].label = "Osoba zmarła"

        self.fields["rok"].label = "Rok"
        self.fields["akt_nr"].label = "Nr aktu"
        self.fields["data_zgonu"].label = "Data zgonu"
        self.fields["miejsce_zgonu"].label = "Miejsce zgonu"
        self.fields["data_pogrzebu"].label = "Data pogrzebu"
        self.fields["cmentarz"].label = "Cmentarz"
        self.fields["uwagi_wew"].label = "Uwagi (wewnętrzne)"

    def clean(self):
        cleaned = super().clean()
        osoba = cleaned.get("osoba")
        if osoba:
            qs = Zgon.objects.filter(osoba=osoba)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Ta osoba ma już wpis zgonu.")
        return cleaned