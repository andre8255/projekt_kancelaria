# konta/tests.py
import os
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from konta.models import LogAkcji, BackupUstawienia
from konta.utils import zapisz_log
from konta.utils_backup import wykonaj_backup_bazy


class LogAkcjiTest(TestCase):
    def test_zapisz_log_creates_entry(self):
        user = User.objects.create_user(username="tester", password="haslo123")
        rf = RequestFactory()
        request = rf.get("/")
        request.user = user

        zapisz_log(request, "TEST_AKCJA", None, opis="Testowy wpis logu")

        self.assertEqual(LogAkcji.objects.count(), 1)
        log = LogAkcji.objects.first()
        self.assertEqual(log.uzytkownik, user)
        self.assertEqual(log.akcja, "TEST_AKCJA")
        self.assertEqual(log.opis, "Testowy wpis logu")


class BackupTest(TestCase):
    def test_backup_creates_file_and_updates_timestamp(self):
        # Upewniamy się, że rekord ustawień istnieje
        ust = BackupUstawienia.get_solo()
        ust.ostatni_backup = None
        ust.save(update_fields=["ostatni_backup"])

        with tempfile.TemporaryDirectory() as tmpdir:
            # Tworzymy "udawany" plik bazy (bo testowa baza Django jest w pamięci)
            fake_db_path = os.path.join(tmpdir, "db.sqlite3")
            with open(fake_db_path, "wb") as f:
                f.write(b"fake sqlite content")

            # Podmieniamy funkcję zwracającą ścieżkę bazy na nasz plik
            with patch("konta.utils_backup._sciezka_pliku_bazy", return_value=fake_db_path):
                # I kierujemy backup do katalogu tymczasowego
                with override_settings(BACKUP_DIR=tmpdir):
                    backup_path = wykonaj_backup_bazy(request=None, powod="RĘCZNY")

            self.assertTrue(os.path.exists(backup_path))

            ust.refresh_from_db()
            self.assertIsNotNone(ust.ostatni_backup)
