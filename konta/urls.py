#konta/urls.py
from django.urls import path
from . import views
from .views import LogowanieView, WylogujView

app_name = 'konta'

urlpatterns = [
    path("logowanie/", LogowanieView.as_view(), name="logowanie"),
    path("wyloguj/",  WylogujView.as_view(),  name="wyloguj"),
    path('backup/', views.pobierz_backup, name='pobierz_backup'),
    path("log-akcji/", views.LogAkcjiListaView.as_view(), name="log_akcji_lista"),
    path("log-akcji/pdf/", views.LogAkcjiPDFView.as_view(), name="log_akcji_pdf"),
]