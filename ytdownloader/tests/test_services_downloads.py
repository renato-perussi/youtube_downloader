"""Testes da orquestracao de downloads."""

from unittest.mock import patch

import pytest

from ytdownloader.models import Download
from ytdownloader.services.downloads import make_progress_hook, run_download_job


@pytest.mark.django_db
def test_progress_hook_updates(tenant, user):
    download = Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=x',
        title='P',
        format_choice='mp4',
        quality='720p',
        status='processing',
    )
    hook = make_progress_hook(download.pk)
    hook({'status': 'downloading', 'total_bytes': 100, 'downloaded_bytes': 25})
    download.refresh_from_db()
    assert download.progress == 25
    hook({'status': 'finished'})
    download.refresh_from_db()
    assert download.progress == 100


@pytest.mark.django_db
def test_run_download_job_success(tenant, user):
    download = Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=x',
        title='Processando...',
        format_choice='mp4',
        quality='720p',
        status='processing',
    )
    fake = {'title': 'Final', 'filename': 'final.mp4', 'file_size': 10}
    with patch('ytdownloader.services.downloads.download_video', return_value=fake):
        run_download_job(download.pk, download.url, 'mp4', '720p', '/tmp')
    download.refresh_from_db()
    assert download.status == 'completed'
    assert download.title == 'Final'
    assert download.progress == 100


@pytest.mark.django_db
def test_run_download_job_failure(tenant, user):
    download = Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=x',
        title='P',
        format_choice='mp4',
        quality='720p',
        status='processing',
    )
    with patch('ytdownloader.services.downloads.download_video', side_effect=Exception('boom')):
        run_download_job(download.pk, download.url, 'mp4', '720p', '/tmp')
    download.refresh_from_db()
    assert download.status == 'failed'
    assert download.error_message
