# slowniki/urls.py

from django.urls import path

from . import views


urlpatterns = [
    # =============================================================================
    # PARAFIE
    # =============================================================================
    path(
        "slowniki/parafie/",
        views.ParafiaListaView.as_view(),
        name="slownik_parafia_lista",
    ),
    path(
        "slowniki/parafie/nowa/",
        views.ParafiaNowaView.as_view(),
        name="slownik_parafia_nowa",
    ),
    path(
        "slowniki/parafie/<int:pk>/edytuj/",
        views.ParafiaEdycjaView.as_view(),
        name="slownik_parafia_edycja",
    ),
    path(
        "slowniki/parafie/<int:pk>/usun/",
        views.ParafiaUsunView.as_view(),
        name="slownik_parafia_usun",
    ),
    path(
        "slowniki/parafie/<int:pk>/",
        views.ParafiaSzczegolyView.as_view(),
        name="slownik_parafia_szczegoly",
    ),
    # =============================================================================
    # DUCHOWNI
    # =============================================================================
    path(
        "slowniki/duchowni/",
        views.DuchownyListaView.as_view(),
        name="slownik_duchowny_lista",
    ),
    path(
        "slowniki/duchowni/nowy/",
        views.DuchownyNowyView.as_view(),
        name="slownik_duchowny_nowy",
    ),
    path(
        "slowniki/duchowni/<int:pk>/edytuj/",
        views.DuchownyEdycjaView.as_view(),
        name="slownik_duchowny_edycja",
    ),
    path(
        "slowniki/duchowni/<int:pk>/usun/",
        views.DuchownyUsunView.as_view(),
        name="slownik_duchowny_usun",
    ),
    path(
        "slowniki/duchowni<int:pk>/",
        views.DuchownySzczegolyView.as_view(),
        name="slownik_duchowny_szczegoly",
    ),
    # =============================================================================
    # WYZNANIA
    # =============================================================================
    path(
        "slowniki/wyznania/",
        views.WyznanieListaView.as_view(),
        name="slownik_wyznanie_lista",
    ),
    path(
        "slowniki/wyznania/nowe/",
        views.WyznanieNoweView.as_view(),
        name="slownik_wyznanie_nowe",
    ),
    path(
        "slowniki/wyznania/<int:pk>/edytuj/",
        views.WyznanieEdycjaView.as_view(),
        name="slownik_wyznanie_edytuj",
    ),
    path(
        "slowniki/wyznania/<int:pk>/usun/",
        views.WyznanieUsunView.as_view(),
        name="slownik_wyznanie_usun",
    ),
]
