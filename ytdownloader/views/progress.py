"""Progresso em tempo real (pagina + JSON)."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, View

from ytdownloader.models import Download
from ytdownloader.services import format_file_size

from .mixins import TenantAwareMixin


class DownloadProgressView(LoginRequiredMixin, TenantAwareMixin, DetailView):
    model = Download
    template_name = 'ytdownloader/progress.html'
    context_object_name = 'download'


class DownloadProgressJsonView(LoginRequiredMixin, View):
    """Endpoint JSON para polling do progresso (substitui a antiga FBV)."""

    def get(self, request, slug, pk):
        download = get_object_or_404(Download, pk=pk, tenant__slug=slug, tenant__user=request.user)
        return JsonResponse(
            {
                'progress': download.progress,
                'status': download.status,
                'error_message': download.error_message if download.is_failed else None,
                'file_size': format_file_size(download.file_size),
            }
        )
