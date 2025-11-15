# konta/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

class RolaWymaganaMixin(LoginRequiredMixin):
    dozwolone_role = None  # np. {Rola.ADMIN, Rola.KSIAZD}

    def dispatch(self, request, *args, **kwargs):
        if self.dozwolone_role is None:
            return super().dispatch(request, *args, **kwargs)

        profil = getattr(request.user, "profil", None)
        if not profil or profil.rola not in self.dozwolone_role:
            raise PermissionDenied("Brak uprawnień do tej sekcji.")
        return super().dispatch(request, *args, **kwargs)
