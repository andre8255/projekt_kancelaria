# osoby/urls.py
from django.urls import path
from . import views

urlpatterns = [
   # path("panel/", views.PanelStartView.as_view(), name="panel_start"),

    path("rodziny/", views.RodzinaListaView.as_view(), name="rodzina_lista"),
    path("rodziny/nowa/", views.RodzinaNowaView.as_view(), name="rodzina_nowa"),
    path("rodziny/<int:pk>/", views.RodzinaSzczegolyView.as_view(), name="rodzina_szczegoly"),
    path("rodziny/<int:pk>/edytuj/", views.RodzinaEdycjaView.as_view(), name="rodzina_edytuj"),
    path("rodziny/<int:pk>/usun/", views.RodzinaUsunView.as_view(), name="rodzina_usun"),
    path("prodziny/<int:rodzina_pk>/dodaj-czlonka/", views.DodajCzlonkaView.as_view(), name="rodzina_dodaj_czlonka"),
    path("rodziny/<int:rodzina_pk>/czlonek/<int:czlonek_pk>/usun/",views.UsunCzlonkaZRodzinyView.as_view(),name="rodzina_usun_czlonka",),
    path("rodziny/czlonkowie/<int:pk>/usun/",views.CzlonkostwoUsunView.as_view(),name="rodzina_czlonek_usun",),
]