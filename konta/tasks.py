# konta/tasks.py
import os
import shutil
import glob
from django.conf import settings
from django.utils import timezone
from .models import BackupUstawienia  # Importujemy model ustawień

def wykonaj_automatyczny_backup():
    try:
        # 1. POBIERANIE USTAWIEŃ
        # Jeśli tabela nie istnieje (np. przed migracją), przerywamy cicho
        try:
            ust = BackupUstawienia.load()
        except Exception:
            return

        if not ust.wlaczony:
            return  # Backup wyłączony w panelu

        # 2. SPRAWDZENIE GODZINY
        teraz = timezone.localtime()
        
        # Jeśli jest wcześniej niż ustalona godzina, nic nie rób
        if teraz.time() < ust.godzina_kopii:
            return

        # 3. KONFIGURACJA ŚCIEŻEK
        db_path = settings.DATABASES['default']['NAME']
        # Pobieramy katalog z ustawień (lub domyślny 'backups')
        backup_dir = os.path.join(settings.BASE_DIR, ust.katalog)
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # 4. NAZWA PLIKU (BEZ SEKUND!)
        # To jest klucz do naprawy błędu. Tworzymy nazwę opartą tylko o DATĘ.
        # Dzięki temu, jeśli skrypt uruchomi się 5 razy w ciągu dnia, 
        # za pierwszym razem utworzy plik, a za kolejnymi 4 razami zobaczy, że już jest.
        data_str = teraz.strftime("%Y-%m-%d")
        filename = f"auto_backup_{data_str}.sqlite3"
        destination = os.path.join(backup_dir, filename)

        # 5. BLOKADA DUPLIKATÓW
        # Jeśli plik z dzisiejszą datą już istnieje -> PRZERYWAMY
        if os.path.exists(destination):
            # print(f"[BACKUP SKIPPED] Kopia na dzień {data_str} już istnieje.")
            return

        # 6. WYKONANIE KOPII
        shutil.copy2(db_path, destination)
        print(f"[BACKUP] Wykonano automatyczną kopię: {filename}")
        
        # 7. ROTACJA (Twoja logika - zachowujemy 5 ostatnich)
        list_of_files = glob.glob(os.path.join(backup_dir, 'auto_backup_*.sqlite3'))
        # Sortowanie po dacie utworzenia
        list_of_files.sort(key=os.path.getctime)
        
        while len(list_of_files) > 5:
            oldest_file = list_of_files.pop(0)
            try:
                os.remove(oldest_file)
                print(f"[BACKUP] Usunięto stary backup: {os.path.basename(oldest_file)}")
            except OSError as e:
                print(f"[BACKUP ERROR] Nie można usunąć pliku {oldest_file}: {e}")
            
    except Exception as e:
        print(f"[BACKUP ERROR] Krytyczny błąd: {e}")