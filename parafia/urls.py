# parafia/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import include, path, reverse

def root_redirect(request):
 
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("panel_start"))
    return HttpResponseRedirect(reverse("konta:logowanie"))

urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("", include("konta.urls")),
    path("panel/cmentarz/", include(("cmentarz.urls", "cmentarz"), namespace="cmentarz")),
    path("panel/", include("osoby.urls")),
    path("panel/", include("rodziny.urls")),
    path("panel/", include("msze.urls")),
    path("panel/", include("sakramenty.urls")),
    path("panel/", include("slowniki.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ===============================
#  Custom 403 – Brak uprawnień
# ===============================

# Django spodziewa się, że ta zmienna będzie zdefiniowana w module urls.py
# i będzie wskazywać na widok obsługujący strony 403.
handler403 = "parafia.views.permission_denied_view"
