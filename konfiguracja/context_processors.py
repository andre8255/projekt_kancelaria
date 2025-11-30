from .models import UstawieniaParafii

def dane_parafii(request):
    """
    Wstrzykuje obiekt 'parafia' do każdego szablonu HTML.
    """
    return {
        'parafia': UstawieniaParafii.load()
    }