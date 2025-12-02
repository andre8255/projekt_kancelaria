#konta/utils_backaup.py
import os
import shutil
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from .models import BackupUstawienia, BackupUstawienia as BU
from .utils import zapisz_log


def _sciezka_pliku_bazy():
    db = settings.DATABASES["default"]
    engine = db["ENGINE"]
    name = db["NAME"]

    if "sqlite" not in engine:
        raise NotImplementedError(
            "Automatyczny backup obsługuje na razie tylko bazę SQLite."
        )

    return name  # pełna ścieżka do pliku bazy sqlite


def _katalog_backupow():
    backup_dir = getattr(settings, "BACKUP_DIR", None)
    if not backup_dir:
        backup_dir = os.path.join(settings.BASE_DIR, "backups")

    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def wykonaj_backup_bazy(request=None, powod="RĘCZNY"):
    """
    Tworzy kopię pliku bazy SQLite w katalogu backups/.
    Zwraca pełną ścieżkę do pliku kopii.
    """
    sciezka_bazy = _sciezka_pliku_bazy()
    katalog = _katalog_backupow()

    teraz = timezone.now()
    znacznik = teraz.strftime("%Y%m%d_%H%M%S")
    nazwa_pliku = f"backup_{znacznik}.sqlite3"
    sciezka_kopii = os.path.join(katalog, nazwa_pliku)

    shutil.copy2(sciezka_bazy, sciezka_kopii)

    ust = BackupUstawienia.get_solo()
    ust.ostatni_backup = teraz
    ust.save(update_fields=["ostatni_backup"])

    if request is not None:
        zapisz_log(
            request,
            "BACKUP_BAZY",
            None,
            opis=f"Wykonano backup bazy ({powod}) do pliku {nazwa_pliku}",
        )

    return sciezka_kopii

def czy_backup_jest_nalezny(ust: BU, teraz=None):
    if not ust.włączony:
        return False

    if teraz is None:
        teraz = timezone.now()

    ostatni = ust.ostatni_backup
    godzina = ust.godzina

    cel_dzis = teraz.replace(
        hour=godzina.hour,
        minute=godzina.minute,
        second=0,
        microsecond=0
    )

    # --- codziennie ---
    if ust.czestotliwosc == BU.CZESTOTLIWOSC_DAILY:
        if not ostatni:
            return teraz >= cel_dzis
        return (ostatni.date() < teraz.date()) and (teraz >= cel_dzis)

    # --- tygodniowo ---
    if ust.czestotliwosc == BU.CZESTOTLIWOSC_WEEKLY:
        mapka = {
            "mon": 0, "tue": 1, "wed": 2,
            "thu": 3, "fri": 4, "sat": 5, "sun": 6,
        }
        target_dow = mapka.get(ust.dzien_tygodnia, 0)
        if teraz.weekday() != target_dow:
            return False
        if not ostatni:
            return teraz >= cel_dzis
        return (ostatni.date() < teraz.date()) and (teraz >= cel_dzis)

    # --- miesięcznie (1. dzień miesiąca) ---
    if ust.czestotliwosc == BU.CZESTOTLIWOSC_MONTHLY:
        if teraz.day != 1:
            return False
        if not ostatni:
            return teraz >= cel_dzis
        ostatni_ym = (ostatni.year, ostatni.month)
        teraz_ym = (teraz.year, teraz.month)
        return (ostatni_ym < teraz_ym) and (teraz >= cel_dzis)

    # Tylko ręcznie
    return False