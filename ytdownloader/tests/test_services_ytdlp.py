"""Testes da integracao yt-dlp (com mocks)."""

from unittest.mock import MagicMock, patch

import pytest

from ytdownloader.services.exceptions import DownloadServiceError
from ytdownloader.services.ytdlp import (
    build_ydl_opts,
    format_video_info,
    get_video_info,
    is_forbidden_error,
)


def test_is_forbidden_error():
    assert is_forbidden_error(Exception('ERROR 403 Forbidden'))
    assert not is_forbidden_error(Exception('timeout'))


def test_format_video_info_defaults():
    info = format_video_info({}, 'https://youtu.be/x')
    assert info['duration_formatted'] == '00:00'
    assert info['channel'] == 'Desconhecido'
    assert info['url'] == 'https://youtu.be/x'


def test_format_video_info_full():
    raw = {
        'title': 'T',
        'thumbnail': 'http://img',
        'duration': 3661,
        'upload_date': '20240101',
        'view_count': 1234,
        'channel': 'Canal',
    }
    info = format_video_info(raw, 'https://youtu.be/x')
    assert info['duration_formatted'] == '1:01:01'
    assert info['upload_date_formatted'] == '01/01/2024'
    assert info['view_count_formatted'] == '1,234'


def test_get_video_info_success():
    with patch('ytdownloader.services.ytdlp.extract_raw_info', return_value={'title': 'T'}):
        info = get_video_info('https://youtu.be/x')
        assert info['title'] == 'T'


def test_get_video_info_failure():
    with (
        patch('ytdownloader.services.ytdlp.extract_raw_info', side_effect=Exception('boom')),
        pytest.raises(DownloadServiceError),
    ):
        get_video_info('https://youtu.be/x')


def test_build_ydl_opts_audio():
    opts = build_ydl_opts('mp3', '192kbps', '/tmp', None, ['default'])
    assert opts['format'] == 'bestaudio/best'
    assert opts['postprocessors'][0]['preferredcodec'] == 'mp3'


def test_build_ydl_opts_video():
    opts = build_ydl_opts('mp4', '720p', '/tmp', MagicMock(), ['default'])
    assert '720' in opts['format']
    assert opts['merge_output_format'] == 'mp4'
    assert len(opts['progress_hooks']) == 1
