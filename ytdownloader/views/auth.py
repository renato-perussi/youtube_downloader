"""Views de autenticacao e redirecionamento (100% CBV)."""

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic import CreateView, RedirectView

from ytdownloader.models import Tenant

INPUT_CLASS = (
    'w-full px-4 py-2.5 bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl '
    'focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent '
    'text-white placeholder-gray-400 transition-all duration-300'
)


class RegisterView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': INPUT_CLASS})
        return form


class LoginRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        tenant = Tenant.resolve(self.request.user)
        return reverse_lazy('home', kwargs={'slug': tenant.slug})


class RootRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            tenant = Tenant.resolve(user)
            return f'/{tenant.slug}/'
        return '/accounts/login/'
