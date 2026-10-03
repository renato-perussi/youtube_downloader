"""Busca + criacao de download."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from ytdownloader.forms import DownloadForm, SearchForm
from ytdownloader.services import create_and_start_download, get_video_info
from ytdownloader.services.exceptions import DownloadServiceError

from .mixins import SearchMixin, TenantAwareMixin


class SearchResultView(LoginRequiredMixin, TenantAwareMixin, SearchMixin, TemplateView):
    template_name = 'ytdownloader/search_result.html'

    def get(self, request, *args, **kwargs):
        if not request.session.get(self.session_key):
            return redirect('home', slug=request.tenant.slug)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video_info = self.request.session.get(self.session_key)
        if not video_info:
            return context
        context['video_info'] = video_info
        context['search_form'] = SearchForm()
        context['download_form'] = DownloadForm(initial={'url': video_info.get('url', '')})
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        if action == 'search':
            return self.handle_search(request)
        if action == 'download':
            return self.handle_download(request)
        return self.get(request, *args, **kwargs)

    def handle_download(self, request):
        download_form = DownloadForm(request.POST)
        if download_form.is_valid():
            data = download_form.cleaned_data
            session_info = request.session.get(self.session_key) or {}
            session_url = session_info.get('url')
            if session_url and data['url'] != session_url:
                download_form.add_error('url', 'URL divergente da busca. Refaca a pesquisa.')
            else:
                try:
                    get_video_info(data['url'])
                    download = create_and_start_download(
                        tenant=request.tenant,
                        user=request.user,
                        url=data['url'],
                        format_choice=data['format_choice'],
                        quality=data['quality'],
                    )
                except DownloadServiceError as exc:
                    download_form.add_error(None, str(exc))
                else:
                    request.session.pop(self.session_key, None)
                    return redirect('download_progress', slug=request.tenant.slug, pk=download.pk)
        video_info = request.session.get(self.session_key)
        search_form = SearchForm(initial={'url': request.POST.get('url', '')})
        return render(
            request,
            self.template_name,
            {'search_form': search_form, 'download_form': download_form, 'video_info': video_info},
        )
