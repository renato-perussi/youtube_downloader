import io
import os
import threading
import zipfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView)

from .forms import DownloadForm, SearchForm
from .models import Download, Tenant
from .utils import download_video, format_file_size, get_video_info


def run_download_thread(
    download_id, url, format_choice, quality, download_dir
):
    def progress_callback(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            pct = int(downloaded / total * 100)
            Download.objects.filter(pk=download_id).update(progress=pct)
        elif d['status'] == 'finished':
            Download.objects.filter(pk=download_id).update(progress=100)

    try:
        result = download_video(
            url,
            format_choice,
            quality,
            download_dir,
            progress_callback=progress_callback,
        )
        relative_path = os.path.join('downloads', result['filename'])
        Download.objects.filter(pk=download_id).update(
            title=result['title'],
            file=relative_path,
            file_size=result['file_size'],
            status=Download.StatusChoices.COMPLETED,
            progress=100,
        )
    except Exception as e:
        Download.objects.filter(pk=download_id).update(
            status=Download.StatusChoices.FAILED,
            error_message=str(e),
        )


class TenantAwareMixin:
    def dispatch(self, request, *args, **kwargs):
        tenant = Tenant.resolve(request.user)
        request.tenant = tenant
        slug = kwargs.get('slug')
        if slug and slug != tenant.slug:
            new_path = request.path.replace(slug, tenant.slug, 1)
            return redirect(new_path)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(tenant=self.request.tenant)


class SearchMixin:
    def _handle_search(self, request):
        search_form = SearchForm(request.POST)
        video_info = request.session.get('download_video_info')

        if search_form.is_valid():
            url = search_form.cleaned_data['url']
            try:
                video_info = get_video_info(url)
                request.session['download_video_info'] = video_info
                return redirect('search_result', slug=request.tenant.slug)
            except Exception as e:
                search_form.add_error(
                    'url', f'Erro ao buscar informações do vídeo: {str(e)}'
                )

        context = {'search_form': search_form}
        if video_info:
            context['video_info'] = video_info
            context['download_form'] = DownloadForm(
                initial={'url': request.POST.get('url', '')},
            )
        return render(request, self.template_name, context)


class RegisterView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update(
                {
                    'class': 'w-full px-4 py-2.5 bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent text-white placeholder-gray-400 transition-all duration-300',
                }
            )
        return form


class DownloadCreateView(
    LoginRequiredMixin, TenantAwareMixin, SearchMixin, TemplateView
):
    template_name = 'ytdownloader/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'search':
            return self._handle_search(request)

        return self.get(request, *args, **kwargs)


class SearchResultView(
    LoginRequiredMixin, TenantAwareMixin, SearchMixin, TemplateView
):
    template_name = 'ytdownloader/search_result.html'

    def get(self, request, *args, **kwargs):
        video_info = request.session.get('download_video_info')
        if not video_info:
            return redirect('home', slug=request.tenant.slug)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video_info = self.request.session.get('download_video_info')

        if not video_info:
            return context

        context['video_info'] = video_info
        context['search_form'] = SearchForm()
        context['download_form'] = DownloadForm(
            initial={'url': video_info.get('url', '')},
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'search':
            return self._handle_search(request)
        elif action == 'download':
            return self._handle_download(request)

        return self.get(request, *args, **kwargs)

    def _handle_download(self, request):
        download_form = DownloadForm(request.POST)

        if download_form.is_valid():
            url = download_form.cleaned_data['url']
            format_choice = download_form.cleaned_data['format_choice']
            quality = download_form.cleaned_data['quality']

            download_dir = os.path.join(settings.MEDIA_ROOT, 'downloads')

            download = Download.objects.create(
                tenant=request.tenant,
                user=request.user,
                url=url,
                title='Processando...',
                format_choice=format_choice,
                quality=quality,
                status=Download.StatusChoices.PROCESSING,
            )

            request.session.pop('download_video_info', None)

            thread = threading.Thread(
                target=run_download_thread,
                args=(download.pk, url, format_choice, quality, download_dir),
            )
            thread.start()

            return redirect(
                'download_progress', slug=request.tenant.slug, pk=download.pk
            )

        video_info = request.session.get('download_video_info')
        search_form = SearchForm(initial={'url': request.POST.get('url', '')})

        return render(
            request,
            self.template_name,
            {
                'search_form': search_form,
                'download_form': download_form,
                'video_info': video_info,
            },
        )


class DownloadHistoryView(LoginRequiredMixin, TenantAwareMixin, ListView):
    model = Download
    template_name = 'ytdownloader/download_list.html'
    context_object_name = 'downloads'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(format_choice__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['has_completed_downloads'] = Download.objects.filter(
            tenant=self.request.tenant,
            status='completed',
            file__isnull=False,
        ).exists()
        return context


class DownloadDetailView(LoginRequiredMixin, TenantAwareMixin, DetailView):
    model = Download
    template_name = 'ytdownloader/download_detail.html'
    context_object_name = 'download'


class DownloadDeleteView(
    LoginRequiredMixin, TenantAwareMixin, SuccessMessageMixin, DeleteView
):
    model = Download
    template_name = 'ytdownloader/download_confirm_delete.html'
    success_message = 'Download excluído com sucesso.'

    def get_success_url(self):
        return reverse('history', args=[self.request.tenant.slug])


class DownloadDeleteAllView(
    LoginRequiredMixin, TenantAwareMixin, TemplateView
):
    template_name = 'ytdownloader/confirm_delete_all.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total'] = Download.objects.filter(
            tenant=self.request.tenant
        ).count()
        return context

    def post(self, request, *args, **kwargs):
        Download.objects.filter(tenant=request.tenant).delete()
        return redirect('history', slug=request.tenant.slug)


class DownloadProgressView(LoginRequiredMixin, TenantAwareMixin, DetailView):
    model = Download
    template_name = 'ytdownloader/progress.html'
    context_object_name = 'download'


@login_required
def download_progress_json(request, slug, pk):
    download = get_object_or_404(Download, pk=pk, tenant__slug=slug)
    return JsonResponse(
        {
            'progress': download.progress,
            'status': download.status,
            'error_message': download.error_message
            if download.status == 'failed'
            else None,
            'file_size': format_file_size(download.file_size),
        }
    )


@login_required
def serve_download(request, pk, slug=None):
    download = get_object_or_404(Download, pk=pk, tenant__slug=slug)

    if not download.file or not os.path.isfile(download.file.path):
        raise FileNotFoundError('Arquivo não encontrado.')

    return FileResponse(
        open(download.file.path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(download.file.name),
    )


@login_required
def download_all(request, slug):
    downloads = Download.objects.filter(
        tenant__slug=slug,
        tenant__user=request.user,
        status='completed',
        file__isnull=False,
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_STORED) as zf:
        for dl in downloads:
            if dl.file and os.path.isfile(dl.file.path):
                zf.write(dl.file.path, os.path.basename(dl.file.name))

    buffer.seek(0)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename='meus_downloads.zip',
    )


@login_required
def login_redirect(request):
    tenant = Tenant.resolve(request.user)
    return redirect('home', slug=tenant.slug)
