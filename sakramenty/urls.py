#sakramenty/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # CHRZEST - zakładam, że to już masz, tylko przykład:
    path("chrzty/", views.ChrzestListaView.as_view(), name="chrzest_lista"),
    path("chrzty/nowy/", views.ChrzestNowyView.as_view(), name="chrzest_dodaj"),
    path("osoby/<int:osoba_pk>/chrzest/nowy/", views.ChrzestNowyView.as_view(), name="chrzest_dodaj_dla_osoby"),  
    path("chrzty/<int:pk>/", views.ChrzestSzczegolyView.as_view(), name="chrzest_szczegoly"),
    path("chrzty/<int:pk>/edytuj/", views.ChrzestEdycjaView.as_view(), name="chrzest_edytuj"),
    path("chrzty/<int:pk>/usun/", views.ChrzestUsunView.as_view(), name="chrzest_usun"),
    
    # KOMUNIA
    path("komunie/", views.KomuniaListaView.as_view(), name="komunia_lista"),
    path("komunie/nowa/", views.KomuniaNowaView.as_view(), name="komunia_dodaj"),
    path("osoby/<int:osoba_pk>/komunia/nowa/", views.KomuniaNowaView.as_view(), name="komunia_dodaj_dla_osoby"),
    path("komunie/<int:pk>/", views.KomuniaSzczegolyView.as_view(), name="komunia_szczegoly"),
    path("komunie/<int:pk>/edytuj/", views.KomuniaEdycjaView.as_view(), name="komunia_edytuj"),
    path("komunie/<int:pk>/usun/", views.KomuniaUsunView.as_view(), name="komunia_usun"),

    # BIERZMOWANIE
    path("bierzmowania/", views.BierzmowanieListaView.as_view(), name="bierzmowanie_lista"),
    path("bierzmowania/nowe/", views.BierzmowanieNoweView.as_view(), name="bierzmowanie_dodaj"),
    path("osoby/<int:osoba_pk>/bierzmowanie/nowe/", views.BierzmowanieNoweView.as_view(), name="bierzmowanie_dodaj_dla_osoby"),
    path("bierzmowania/<int:pk>/", views.BierzmowanieSzczegolyView.as_view(), name="bierzmowanie_szczegoly"),
    path("bierzmowania/<int:pk>/edytuj/", views.BierzmowanieEdycjaView.as_view(), name="bierzmowanie_edytuj"),
    path("bierzmowania/<int:pk>/usun/", views.BierzmowanieUsunView.as_view(), name="bierzmowanie_usun"),

    # MAŁŻEŃSTWA
    path("malzenstwa/", views.MalzenstwoListaView.as_view(), name="malzenstwo_lista"),
    path("malzenstwa/nowe/", views.MalzenstwoNoweView.as_view(), name="malzenstwo_dodaj"),
    path("osoby/<int:osoba_pk>/malzenstwo/nowe/", views.MalzenstwoNoweView.as_view(), name="malzenstwo_dodaj_dla_osoby"),
    path("malzenstwa/<int:pk>/", views.MalzenstwoSzczegolyView.as_view(), name="malzenstwo_szczegoly"),
    path("malzenstwa/<int:pk>/edytuj/", views.MalzenstwoEdycjaView.as_view(), name="malzenstwo_edytuj"),
    path("malzenstwa/<int:pk>/usun/", views.MalzenstwoUsunView.as_view(), name="malzenstwo_usun"),

    # NAMASZCZENIA
    path("namaszczenia/", views.NamaszczenieListaView.as_view(), name="namaszczenie_lista"),
    path("namaszczenia/nowe/", views.NamaszczenieNoweView.as_view(), name="namaszczenie_dodaj"),
    path("osoby/<int:osoba_pk>/namaszczenie/nowe/", views.NamaszczenieNoweView.as_view(), name="namaszczenie_dodaj_dla_osoby"),
    path("namaszczenia/<int:pk>/", views.NamaszczenieSzczegolyView.as_view(), name="namaszczenie_szczegoly"),
    path("namaszczenia/<int:pk>/edytuj/", views.NamaszczenieEdycjaView.as_view(), name="namaszczenie_edytuj"),
    path("namaszczenia/<int:pk>/usun/", views.NamaszczenieUsunView.as_view(), name="namaszczenie_usun"),

    # ZGONY
    path("zgony/", views.ZgonListaView.as_view(), name="zgon_lista"),
    path("zgony/nowy/", views.ZgonNowyView.as_view(), name="zgon_dodaj"),
    path("osoby/<int:osoba_pk>/zgon/nowy/", views.ZgonNowyView.as_view(), name="zgon_dodaj_dla_osoby"),
    path("zgony/<int:pk>/", views.ZgonSzczegolyView.as_view(), name="zgon_szczegoly"),
    path("zgony/<int:pk>/edytuj/", views.ZgonEdycjaView.as_view(), name="zgon_edytuj"),
    path("zgony/<int:pk>/usun/", views.ZgonUsunView.as_view(), name="zgon_usun"),

    # --- DRUKI (widoki "print-friendly") ---

    path("panel/chrzty/<int:pk>/druk/", views.ChrzestDrukView.as_view(), name="chrzest_druk"),
    path("chrzty/lista/druk/", views.ChrzestListaDrukView.as_view(), name="chrzest_lista_druk"),
    path("panel/komunie/<int:pk>/druk/", views.KomuniaDrukView.as_view(), name="komunia_druk"),
    path("komunie/lista/druk/", views.KomuniaListaDrukView.as_view(), name="komunia_lista_druk"),
    path("panel/bierzmowania/<int:pk>/druk/", views.BierzmowanieDrukView.as_view(), name="bierzmowanie_druk"),
    path("bierzmowania/lista/druk/", views.BierzmowanieListaDrukView.as_view(), name="bierzmowanie_lista_druk"),
    path("panel/malzenstwa/<int:pk>/druk/", views.MalzenstwoDrukView.as_view(), name="malzenstwo_druk"),
    path("malzenstwa/lista/druk/", views.MalzenstwoListaDrukView.as_view(), name="malzenstwo_lista_druk"),
    path("panel/namaszczenie/<int:pk>/druk/", views.NamaszczenieDrukView.as_view(), name="namaszczenie_druk"),
    path("namaszczenia/lista/druk/", views.NamaszczenieListaDrukView.as_view(), name="namaszczenie_lista_druk"),
    path("panel/zgony/<int:pk>/druk/", views.ZgonDrukView.as_view(), name="zgon_druk"),
    path("zgony/lista/druk/", views.ZgonListaDrukView.as_view(), name="zgon_lista_druk"),

    # --- PDFy ---
    path("chrzest/<int:pk>/pdf/", views.ChrzestPDFView.as_view(), name="chrzest_pdf"),
    path("chrzty/pdf/", views.ChrzestListaPDFView.as_view(), name="chrzest_lista_pdf"),
    path("komunia/<int:pk>/pdf/", views.KomuniaPDFView.as_view(), name="komunia_pdf"),
    path("komunie/pdf/", views.KomuniaListaPDFView.as_view(), name="komunia_lista_pdf"),
    path("bierzmowanie/<int:pk>/pdf/", views.BierzmowaniePDFView.as_view(), name="bierzmowanie_pdf"),
    path("bierzmowania/pdf/", views.BierzmowanieListaPDFView.as_view(), name="bierzmowanie_lista_pdf"),
    path("malzenstwo/<int:pk>/pdf/", views.MalzenstwoPDFView.as_view(), name="malzenstwo_pdf"),
    path("malzenstwa/pdf/", views.MalzenstwoListaPDFView.as_view(), name="malzenstwo_lista_pdf"),
    path("namaszczenie/<int:pk>/pdf/", views.NamaszczeniePDFView.as_view(), name="namaszczenie_pdf"),
    path("namaszczenia/pdf/", views.NamaszczenieListaPDFView.as_view(), name="namaszczenie_lista_pdf"),
    path("zgon/<int:pk>/pdf/", views.ZgonPDFView.as_view(), name="zgon_pdf"),
    path("zgony/pdf/", views.ZgonListaPDFView.as_view(), name="zgon_lista_pdf"),
]

