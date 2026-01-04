#konta\utils.py
from django.contrib.auth.models import Group
from typing import Optional
from django.http import HttpRequest

from .models import LogAkcji

ROLE_ADMIN       = "Admin"
ROLE_KSIAZD      = "Ksiądz"
ROLE_SEKRETARIAT = "Sekretariat"

def user_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()

def zapisz_log(
    request: Optional[HttpRequest],
    akcja: str,
    obiekt=None,
    opis: str = ""
) -> None:
    """
    Prosty helper zapisujący wpis w logu akcji.

    :param request: obiekt HttpRequest (może być None)
    :param akcja: krótki kod akcji, np. 'DODANIE_OSOBY'
    :param obiekt: obiekt Django (np. instancja Osoba), z którego weźmiemy nazwę modelu i pk
    :param opis: dodatkowy opis, np. 'Dodano osobę Jana Kowalskiego'
    """

    user = None
    if request is not None and hasattr(request, "user") and request.user.is_authenticated:
        user = request.user

    model_name = ""
    obiekt_id = None
    if obiekt is not None:
        model_name = obiekt.__class__.__name__
        obiekt_id = getattr(obiekt, "pk", None)

    LogAkcji.objects.create(
        uzytkownik=user,
        akcja=akcja,
        model=model_name,
        obiekt_id=obiekt_id,
        opis=opis,
    )