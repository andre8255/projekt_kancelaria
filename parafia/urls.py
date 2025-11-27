#parafia/urls.py
from django.contrib import admin
from django.urls import path, include, reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.conf.urls.static import static

def root_redirect(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("panel_start"))
    return HttpResponseRedirect(reverse("logowanie"))

urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("", include("konta.urls")),
    path('konta/', include('konta.urls')),
    path("panel/", include("osoby.urls")),
    path("panel/", include("rodziny.urls")),
    path("panel/", include("msze.urls")),
    path("panel/", include("sakramenty.urls")),
    path("panel/", include("slowniki.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)