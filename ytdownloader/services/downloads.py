"""Orquestracao de downloads em background via threading."""

import contextlib
import logging
import os
import threading

from django.conf import settings
from django.db import close_old_connections

from ytdownloader.models import Download
from ytdownloader.models.choices import DownloadStatus

from .exceptions import DownloadServiceError, safe_error_message
from .ytdlp import download_video

logger = logging.getLogger(__name__)

_DOWNLOAD_SEMAPHORE = threading.BoundedSemaphore(2)
MAX_CONCURRENT_DOWNLOADS = 2


def make_progress_hook(download_id):
    """Cria hook do yt-dlp que atualiza o progresso no banco."""

    def _hook(payload):
        if payload.get('status') == 'downloading':
            total = payload.get('total_bytes') or payload.get('total_bytes_estimate') or 1
            done = payload.get('downloaded_bytes', 0)
            pct = int(done / total * 100)
            Download.objects.filter(pk=download_id).update(progress=pct)
        elif payload.get('status') == 'finished':
            Download.objects.filter(pk=download_id).update(progress=100)

    return _hook


def run_download_job(download_id, url, format_choice, quality, download_dir):
    """Executa o download e atualiza o registro. Roda dentro da thread."""
    close_old_connections()
    try:
        result = download_video(
            url,
            format_choice,
            quality,
            download_dir,
            progress_callback=make_progress_hook(download_id),
            download_id=download_id,
        )
        relative_path = os.path.join('downloads', result['filename'])
        Download.objects.filter(pk=download_id).update(
            title=result['title'],
            file=relative_path,
            file_size=result['file_size'],
            status=DownloadStatus.COMPLETED,
            progress=100,
        )
    except Exception as exc:
        detail = safe_error_message(str(exc))
        logger.warning('Download %s falhou: %s', download_id, detail)
        Download.objects.filter(pk=download_id).update(
            status=DownloadStatus.FAILED,
            error_message=detail,
        )
    finally:
        close_old_connections()
        with contextlib.suppress(ValueError):
            _DOWNLOAD_SEMAPHORE.release()


def download_directory():
    """Resolve o diretorio de midia para downloads."""
    path = os.path.join(settings.MEDIA_ROOT, 'downloads')
    os.makedirs(path, exist_ok=True)
    return path


def create_and_start_download(*, tenant, user, url, format_choice, quality):
    """Cria o registro e inicia o processamento em background.

    Nota: semaforo e por processo. Com gunicorn --workers 3 o limite real e 2 por worker.
    Para limite global use Celery + Redis (ver README roadmap).
    """
    if not _DOWNLOAD_SEMAPHORE.acquire(blocking=False):
        raise DownloadServiceError('Muitos downloads simultaneos. Tente novamente em instantes.')
    try:
        download = Download.objects.create(
            tenant=tenant,
            user=user,
            url=url,
            title='Processando...',
            format_choice=format_choice,
            quality=quality,
            status=DownloadStatus.PROCESSING,
        )
    except Exception:
        with contextlib.suppress(ValueError):
            _DOWNLOAD_SEMAPHORE.release()
        raise
    thread = threading.Thread(
        target=run_download_job,
        args=(
            download.pk,
            download.url,
            download.format_choice,
            download.quality,
            download_directory(),
        ),
        daemon=True,
    )
    thread.start()
    return download
