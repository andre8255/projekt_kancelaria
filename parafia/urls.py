#parafia/urls.py
from django.contrib import admin
from django.urls import path, include, reverse
from django.http import HttpResponseRedirect

def root_redirect(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("panel_start"))
    return HttpResponseRedirect(reverse("logowanie"))

urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("", include("konta.urls")),
    path("panel/", include("osoby.urls")),
    path("panel/", include("rodziny.urls")),
    path("panel/", include("msze.urls")),
    path("panel/", include("sakramenty.urls")),
    path("panel/", include("slowniki.urls")),
]