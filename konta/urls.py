#konta/urls.py
from django.urls import path
from .views import LogowanieView, WylogujView

urlpatterns = [
    path("logowanie/", LogowanieView.as_view(), name="logowanie"),
    path("wyloguj/",  WylogujView.as_view(),  name="wyloguj"),
]