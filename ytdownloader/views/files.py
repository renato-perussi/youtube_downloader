"""Entrega de arquivos (download unico e ZIP)."""

import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views import View

from ytdownloader.models import Download
from ytdownloader.services import build_zip_buffer


class ServeDownloadView(LoginRequiredMixin, View):
    """Serve o arquivo do download como anexo."""

    def get(self, request, slug, pk):
        download = get_object_or_404(Download, pk=pk, tenant__slug=slug, tenant__user=request.user)
        if not download.file or not os.path.isfile(download.file.path):
            raise Http404('Arquivo não encontrado.')
        try:
            handle = open(download.file.path, 'rb')  # noqa: SIM115 - FileResponse fecha o handle
        except OSError as err:
            raise Http404('Arquivo não encontrado.') from err
        try:
            return FileResponse(
                handle,
                as_attachment=True,
                filename=os.path.basename(download.file.name),
            )
        except Exception:
            handle.close()
            raise


class DownloadAllView(LoginRequiredMixin, View):
    """Gera um ZIP com todos os downloads concluidos do tenant."""

    def get(self, request, slug):
        downloads = (
            Download.objects.filter(tenant__slug=slug, tenant__user=request.user)
            .completed()
            .order_by('-created_at')
        )
        buffer = build_zip_buffer(downloads)
        return FileResponse(buffer, as_attachment=True, filename='meus_downloads.zip')
