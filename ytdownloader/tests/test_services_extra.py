"""Cobertura extra: fallback, limites e semaforo."""

import contextlib
from unittest.mock import patch

import pytest
from yt_dlp.utils import DownloadError

from ytdownloader.services.downloads import _DOWNLOAD_SEMAPHORE, create_and_start_download
from ytdownloader.services.exceptions import DownloadServiceError, safe_error_message
from ytdownloader.services.ytdlp import download_video, get_video_info


def test_safe_message_variants():
    assert (
        safe_error_message('Token expired sig = xyz')
        == 'Falha no download. Tente outro formato/qualidade.'
    )
    assert (
        safe_error_message('https://evil.com/?ip=1.2.3.4')
        == 'Falha no download. Tente outro formato/qualidade.'
    )


def test_get_video_info_rejects_long():
    raw = {'title': 'Long', 'duration': 3 * 60 * 60}
    with (
        patch('ytdownloader.services.ytdlp.extract_raw_info', return_value=raw),
        pytest.raises(DownloadServiceError, match='longo'),
    ):
        get_video_info('https://www.youtube.com/watch?v=x')


def test_get_video_info_rejects_live():
    raw = {'title': 'Live', 'duration': 0, 'is_live': True, 'live_status': 'is_live'}
    with (
        patch('ytdownloader.services.ytdlp.extract_raw_info', return_value=raw),
        pytest.raises(DownloadServiceError, match='vivo'),
    ):
        get_video_info('https://www.youtube.com/watch?v=x')


def test_download_video_fallback_403():
    with (
        patch('ytdownloader.services.ytdlp.execute_download') as mock_exec,
    ):
        mock_exec.side_effect = [
            DownloadError('ERROR 403 Forbidden'),
            {'title': 'T', 'filename': 't.mp4', 'file_size': 1},
        ]
        result = download_video('https://www.youtube.com/watch?v=x', 'mp4', '720p', '/tmp')
        assert result['title'] == 'T'
        assert mock_exec.call_count == 2


def test_download_video_no_retry_for_other_error():
    with (
        patch(
            'ytdownloader.services.ytdlp.execute_download',
            side_effect=DownloadError('Private video'),
        ),
        pytest.raises(DownloadServiceError),
    ):
        download_video('https://www.youtube.com/watch?v=x', 'mp4', '720p', '/tmp')


@pytest.mark.django_db
def test_semaphore_limit(tenant, user):
    acquired = []
    try:
        acquired.append(_DOWNLOAD_SEMAPHORE.acquire(blocking=False))
        acquired.append(_DOWNLOAD_SEMAPHORE.acquire(blocking=False))
        assert not _DOWNLOAD_SEMAPHORE.acquire(blocking=False)
        with pytest.raises(DownloadServiceError, match='simultaneos'):
            create_and_start_download(
                tenant=tenant,
                user=user,
                url='https://www.youtube.com/watch?v=x',
                format_choice='mp4',
                quality='720p',
            )
    finally:
        for _ in acquired:
            with contextlib.suppress(ValueError):
                _DOWNLOAD_SEMAPHORE.release()
