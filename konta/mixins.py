# konta/mixins.py
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin

class RolaWymaganaMixin(LoginRequiredMixin):
    dozwolone_role = []  # np. [Rola.ADMIN, Rola.KSIADZ, Rola.SEKRETARIAT]

    def dispatch(self, request, *args, **kwargs):
        # 1. Niezalogowani – klasyczne zachowanie
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 2. SUPERUSER – zawsze pełny dostęp
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # 3. Rola jest w profilu użytkownika (User -> Profil)
        profil = getattr(request.user, "profil", None)
        rola_uzytkownika = getattr(profil, "rola", None)

        # 4. Jeśli wymagane role są ustawione, sprawdzamy
        if self.dozwolone_role and rola_uzytkownika not in self.dozwolone_role:
            raise PermissionDenied("Brak uprawnień do tej sekcji.")

        return super().dispatch(request, *args, **kwargs)
