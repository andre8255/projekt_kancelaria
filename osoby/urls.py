# osoby/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.PanelStartView.as_view(), name="panel_start"),

    path("osoby/", views.OsobaListaView.as_view(), name="osoba_lista"),
    path("osoby/nowa/", views.OsobaNowaView.as_view(), name="osoba_nowa"),
    path("osoby/<int:pk>/", views.OsobaSzczegolyView.as_view(), name="osoba_szczegoly"),
    path("osoby/<int:pk>/edytuj/", views.OsobaEdycjaView.as_view(), name="osoba_edytuj"),
    path("osoby/<int:pk>/usun/", views.OsobaUsunView.as_view(), name="osoba_usun"),
]
