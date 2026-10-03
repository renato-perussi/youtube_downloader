"""Home do tenant com formulario de busca."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from ytdownloader.forms import SearchForm

from .mixins import SearchMixin, TenantAwareMixin


class DownloadCreateView(LoginRequiredMixin, TenantAwareMixin, SearchMixin, TemplateView):
    template_name = 'ytdownloader/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm()
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'search':
            return self.handle_search(request)
        return self.get(request, *args, **kwargs)
