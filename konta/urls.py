#konta/urls.py
from django.urls import path
from . import views
from .views import LogowanieView, WylogujView

app_name = 'konta'

urlpatterns = [
    path("logowanie/", LogowanieView.as_view(), name="logowanie"),
    path("wyloguj/",  WylogujView.as_view(),  name="wyloguj"),
    path('backup/', views.pobierz_backup, name='pobierz_backup'),
]