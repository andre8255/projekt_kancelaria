from django.views import View
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.messages import get_messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages



class LogowanieView(LoginView):
    template_name = "konta/logowanie.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        # skonsumuj ewentualne stare wiadomości (np. „Wylogowano.”)
        list(get_messages(self.request))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("panel_start")

class WylogujView(View):
    def post(self, request):
        logout(request)
        messages.success(request, "Wylogowano.")
        return redirect("logowanie")