# cmentarz/urls.py

from django.urls import path

from . import views


app_name = "cmentarz"

urlpatterns = [
    # =============================================================================
    # GROBY (CRUD)
    # =============================================================================
    path("", views.GrobListaView.as_view(), name="grob_lista"),
    path("nowy/", views.GrobNowyView.as_view(), name="grob_nowy"),
    path("<int:pk>/", views.GrobSzczegolyView.as_view(), name="grob_szczegoly"),
    path("<int:pk>/edytuj/", views.GrobEdycjaView.as_view(), name="grob_edytuj"),
    path("<int:pk>/usun/", views.GrobUsunView.as_view(), name="grob_usun"),
    # =============================================================================
    # POCHOWANI (powiązania osób z grobem)
    # =============================================================================
    # Dodawanie osoby do konkretnego grobu
    path(
        "<int:grob_pk>/dodaj-osobe/",
        views.PochowanyNowyView.as_view(),
        name="pochowany_nowy",
    ),
    # Usuwanie wpisu pochówku
    path(
        "pochowany/<int:pk>/usun/",
        views.PochowanyUsunView.as_view(),
        name="pochowany_usun",
    ),
    # =============================================================================
    # WYDRUKI (PDF)
    # =============================================================================
    path("<int:pk>/pdf/", views.GrobPDFView.as_view(), name="grob_pdf"),
    # =============================================================================
    # SEKTORY
    # =============================================================================
    path("sektory/", views.SektorListaView.as_view(), name="sektor_lista"),
    path("sektory/nowy/", views.SektorNowyView.as_view(), name="sektor_nowy"),
]
