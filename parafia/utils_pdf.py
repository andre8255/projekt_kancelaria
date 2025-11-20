# parafia/utils_pdf.py
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings

def render_to_pdf(template_src, context_dict={}, filename="dokument.pdf"):
    """
    Renderuje szablon HTML do pliku PDF i zwraca jako odpowiedź HTTP.
    """
    # Renderujemy HTML jako string
    html_string = render_to_string(template_src, context_dict)
    
    # Tworzymy obiekt HTML z WeasyPrint, ustawiając base_url dla plików statycznych (logo, css)
    html = HTML(string=html_string, base_url=str(settings.BASE_DIR))
    
    # Generujemy PDF
    pdf_file = html.write_pdf()
    
    # Tworzymy odpowiedź HTTP z plikiem PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    
    # Ustawiamy nagłówek, żeby przeglądarka wiedziała, jak nazwać plik
    # 'inline' = otwórz w przeglądarce, 'attachment' = pobierz na dysk
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response