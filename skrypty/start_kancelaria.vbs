Set shell = CreateObject("WScript.Shell")

' polecenie uruchomienia serwera Django z venv
cmd = """D:\aplikacja\projekt_kancelaria\.venv\Scripts\python.exe"" " & _
      """D:\aplikacja\projekt_kancelaria\manage.py"" runserver 127.0.0.1:8000"

' start serwera w tle (0 = brak okna, False = nie czekamy na zakończenie)
shell.Run cmd, 0, False

' 3 sekundy na rozruch serwera
WScript.Sleep 3000

' otwarcie strony logowania w domyślnej przeglądarce
shell.Run "http://127.0.0.1:8000/logowanie/"