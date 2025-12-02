from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profil
from .models import LogAkcji, BackupUstawienia

# Usuń domyślną rejestrację User, jeśli już istnieje
admin.site.unregister(User)

# Zdefiniuj "wbudowany" edytor dla Profilu
class ProfilInline(admin.StackedInline):
    model = Profil
    can_delete = False
    verbose_name_plural = 'Profile'

# Zdefiniuj nowy panel admina dla Użytkownika
class UserAdmin(BaseUserAdmin):
    inlines = (ProfilInline,)

# Zarejestruj ponownie Użytkownika z wbudowanym Profilem
admin.site.register(User, UserAdmin)

# Możesz też zarejestrować Profil osobno (opcjonalnie)
@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('uzytkownik', 'rola')
    list_filter = ('rola',)

@admin.register(LogAkcji)
class LogAkcjiAdmin(admin.ModelAdmin):
    list_display = ("kiedy", "uzytkownik", "akcja", "model", "obiekt_id")
    list_filter = ("akcja", "model", "uzytkownik")
    search_fields = ("opis", "model", "akcja", "uzytkownik__username")
    readonly_fields = ("kiedy", "uzytkownik", "akcja", "model", "obiekt_id", "opis")

    def has_add_permission(self, request):
        # nie dodajemy logów ręcznie
        return False

    def has_change_permission(self, request, obj=None):
        # nie edytujemy logów
        return False

@admin.register(BackupUstawienia)
class BackupUstawieniaAdmin(admin.ModelAdmin):
    list_display = ("id", "wlaczony", "czestotliwosc", "dzien_tygodnia", "godzina")
    list_filter = ("wlaczony", "czestotliwosc", "dzien_tygodnia")