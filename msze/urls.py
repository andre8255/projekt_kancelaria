#msze/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("msze/", views.MszaListaView.as_view(), name="msza_lista"),
    path("msze/nowa/", views.MszaNowaView.as_view(), name="msza_nowa"),
    path("msze/<int:pk>/", views.MszaSzczegolyView.as_view(), name="msza_szczegoly"),
    path("msze/<int:pk>/edytuj/", views.MszaEdycjaView.as_view(), name="msza_edytuj"),
    path("msze/<int:pk>/usun/", views.MszaUsunView.as_view(), name="msza_usun"),
    path("msze/<int:msza_pk>/intencja/nowa/",views.IntencjaNowaView.as_view(),name="intencja_nowa"),
    path("panel/intencje/<int:pk>/edytuj/", views.IntencjaEdycjaView.as_view(), name="intencja_edytuj"), 
    path("panel/intencje/<int:pk>/usun/", views.IntencjaUsunView.as_view(), name="intencja_usun"),

    path("msze/kalendarz/", views.KalendarzMszyView.as_view(), name="msza_kalendarz"),
    path("msze/kalendarz/dane/", views.kalendarz_mszy_dane, name="msza_kalendarz_dane"),
    path("lista/pdf/", views.MszaListaPDFView.as_view(), name="msza_lista_pdf"),
]
