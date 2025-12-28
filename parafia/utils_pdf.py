# sakramenty/utils_pdf.py
from __future__ import annotations

from typing import Any, Dict, Optional

from django.apps import apps
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML


def render_to_pdf(
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    filename: str = "dokument.pdf",
) -> HttpResponse:
    """
    Renderuje szablon HTML do PDF przy użyciu WeasyPrint i zwraca HttpResponse.

    - Automatycznie dołącza do kontekstu obiekt UstawieniaParafii jako 'parafia'
      (o ile klucz 'parafia' nie został już podany).
    - `template_name` – ścieżka do szablonu (np. 'sakramenty/chrzest_pdf.html')
    - `context` – słownik kontekstu przekazywany do render_to_string
    - `filename` – nazwa pliku proponowana przy pobieraniu / otwieraniu PDF-a
    """

    if context is None:
        context = {}

    # Dynamiczne pobranie modelu, aby uniknąć problemów z cyklicznymi importami
    UstawieniaParafii = apps.get_model("konfiguracja", "UstawieniaParafii")
    parafia_obj = UstawieniaParafii.load()

    # Jeśli w kontekście nie ma jeszcze klucza 'parafia', wstrzykujemy z ustawień
    context.setdefault("parafia", parafia_obj)

    # Render HTML z szablonu
    html_string = render_to_string(template_name, context)

    # Generowanie PDF z HTML
    html = HTML(string=html_string, base_url=str(settings.BASE_DIR))
    pdf_file = html.write_pdf()

    # Odpowiedź HTTP z PDF-em
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'

    return response
