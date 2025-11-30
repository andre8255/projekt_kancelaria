from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings
# Import modelu (wewnątrz funkcji, by uniknąć cyklicznych importów przy starcie)
from django.apps import apps 

def render_to_pdf(template_src, context_dict={}, filename="dokument.pdf"):
    # Dynamiczne pobranie modelu
    UstawieniaParafii = apps.get_model('konfiguracja', 'UstawieniaParafii')
    parafia_obj = UstawieniaParafii.load()

    # Dodajemy dane parafii do kontekstu PDF-a, jeśli ich tam nie ma
    if 'parafia' not in context_dict:
        context_dict['parafia'] = parafia_obj

    html_string = render_to_string(template_src, context_dict)
    
    # ... reszta bez zmian ...
    html = HTML(string=html_string, base_url=str(settings.BASE_DIR))
    pdf_file = html.write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response