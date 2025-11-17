from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profil

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