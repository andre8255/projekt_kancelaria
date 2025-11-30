from django.contrib import admin
from .models import UstawieniaParafii

@admin.register(UstawieniaParafii)
class UstawieniaParafiiAdmin(admin.ModelAdmin):
    # Blokujemy usuwanie rekordu, żeby system się nie posypał
    def has_delete_permission(self, request, obj=None):
        return False

    # Blokujemy dodawanie, jeśli już coś jest w bazie
    def has_add_permission(self, request):
        return not UstawieniaParafii.objects.exists()