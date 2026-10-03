"""Mixins compartilhados das views multi-tenant."""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from ytdownloader.forms import DownloadForm, SearchForm
from ytdownloader.models import Tenant
from ytdownloader.services import DownloadServiceError, get_video_info
from ytdownloader.services.exceptions import safe_error_message


class TenantAwareMixin:
    """Garante isolamento por tenant e expoe request.tenant."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())
        tenant = Tenant.resolve(request.user)
        request.tenant = tenant
        slug = kwargs.get('slug')
        if slug and slug != tenant.slug:
            kwargs['slug'] = tenant.slug
            match = getattr(request, 'resolver_match', None)
            if match and match.url_name:
                new_path = reverse(match.url_name, kwargs={**match.kwargs, 'slug': tenant.slug})
                query = request.META.get('QUERY_STRING', '')
                if query:
                    new_path = f'{new_path}?{query}'
                return redirect(new_path)
            new_path = request.path.replace(slug, tenant.slug, 1)
            query = request.META.get('QUERY_STRING', '')
            if query:
                new_path = f'{new_path}?{query}'
            return redirect(new_path)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(tenant=self.request.tenant)

    def get_tenant(self):
        return self.request.tenant


class SearchMixin:
    """Compartilha a logica de busca de video via sessao."""

    session_key = 'download_video_info'
    template_name = ''

    def fetch_video_info(self, request, search_form):
        url = search_form.cleaned_data['url']
        try:
            video_info = get_video_info(url)
        except DownloadServiceError as exc:
            search_form.add_error('url', str(exc))
            return None
        except Exception as exc:
            search_form.add_error('url', safe_error_message(str(exc)))
            return None
        request.session[self.session_key] = video_info
        return video_info

    def handle_search(self, request):
        search_form = SearchForm(request.POST)
        video_info = request.session.get(self.session_key)
        if search_form.is_valid():
            fetched = self.fetch_video_info(request, search_form)
            if fetched is not None:
                return redirect('search_result', slug=request.tenant.slug)
        context = {'search_form': search_form}
        if video_info:
            context['video_info'] = video_info
            context['download_form'] = DownloadForm(initial={'url': request.POST.get('url', '')})
        return render(request, self.template_name, context)

    def warn_no_video_info(self, request):
        messages.warning(request, 'Informe um link do YouTube para continuar.')
