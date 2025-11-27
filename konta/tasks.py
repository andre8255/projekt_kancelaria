# konta/tasks.py
import os
import shutil
from datetime import datetime
from django.conf import settings
import glob

def wykonaj_automatyczny_backup():
    # 1. Konfiguracja ścieżek
    db_path = settings.DATABASES['default']['NAME']
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    
    # Upewnij się, że folder na kopie istnieje
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # 2. Nazwa pliku z datą i godziną
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"auto_backup_{timestamp}.sqlite3"
    destination = os.path.join(backup_dir, filename)

    try:
        # 3. Wykonanie kopii (kopiowanie pliku bazy)
        shutil.copy2(db_path, destination)
        print(f"[BACKUP] Wykonano automatyczną kopię: {filename}")
        
        # 4. Rotacja (usuwanie starych kopii) - zostawiamy np. 10 ostatnich
        # Znajdź wszystkie pliki backupu
        list_of_files = glob.glob(os.path.join(backup_dir, 'auto_backup_*.sqlite3'))
        # Posortuj od najstarszego do najnowszego
        list_of_files.sort(key=os.path.getctime)
        
        # Jeśli jest więcej niż 10 plików, usuń najstarsze
        while len(list_of_files) > 10:
            oldest_file = list_of_files.pop(0)
            os.remove(oldest_file)
            print(f"[BACKUP] Usunięto stary backup: {oldest_file}")
            
    except Exception as e:
        print(f"[BACKUP ERROR] Nie udało się wykonać kopii: {e}")