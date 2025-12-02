# konta/mixins.py
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Rola  # jeśli używasz enumu Rola (ADMIN, KSIADZ, itp.)

class RolaWymaganaMixin(LoginRequiredMixin):
    dozwolone_role = []  # np. [Rola.ADMIN, Rola.KSIAZD, Rola.SEKRETARIAT]

    def dispatch(self, request, *args, **kwargs):
        # 1. Niezalogowani – klasyczne zachowanie
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 2. SUPERUSER (admin z /admin/) – ma zawsze pełny dostęp
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # 3. Zwykły użytkownik – sprawdzamy 'rola'
        rola_uzytkownika = getattr(request.user, "rola", None)

        # Jeśli lista dozwolonych ról nie jest pusta, to sprawdzamy
        if self.dozwolone_role and rola_uzytkownika not in self.dozwolone_role:
            # to trafi w 403.html z naszym ładnym komunikatem
            raise PermissionDenied("Brak uprawnień do tej sekcji.")

        return super().dispatch(request, *args, **kwargs)
