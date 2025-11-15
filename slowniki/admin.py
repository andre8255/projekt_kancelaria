from django.contrib import admin
from .models import Parafia, Duchowny, Wyznanie


@admin.register(Parafia)
class ParafiaAdmin(admin.ModelAdmin):
    list_display = ("miejscowosc", "nazwa", "diecezja")
    search_fields = ("nazwa", "miejscowosc", "diecezja")
    list_filter = ("diecezja",)


@admin.register(Duchowny)
class DuchownyAdmin(admin.ModelAdmin):
    list_display = ("imie_nazwisko", "tytul", "parafia", "aktywny")
    list_filter = ("aktywny", "tytul")
    search_fields = ("imie_nazwisko",)


@admin.register(Wyznanie)
class WyznanieAdmin(admin.ModelAdmin):
    list_display = ("nazwa",)
    search_fields = ("nazwa",)
