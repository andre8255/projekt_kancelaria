from typing import Optional
from django.http import HttpRequest
from .models import LogAkcji

def zapisz_log(
    request: Optional[HttpRequest],
    akcja: str,
    obiekt=None,
    opis: str = "",
    model: str = "",
    obiekt_id: int | None = None,
) -> None:
    user = None
    if request is not None and hasattr(request, "user") and request.user.is_authenticated:
        user = request.user

    # domyślnie bierzemy z obiektu
    model_name = ""
    obj_id = None
    if obiekt is not None:
        model_name = obiekt.__class__.__name__
        obj_id = getattr(obiekt, "pk", None)

    # ale jeśli podano jawnie model/obiekt_id – nadpisz
    if model:
        model_name = model
    if obiekt_id is not None:
        obj_id = obiekt_id

    LogAkcji.objects.create(
        uzytkownik=user,
        akcja=akcja,
        model=model_name,
        obiekt_id=obj_id,
        opis=opis,
    )
