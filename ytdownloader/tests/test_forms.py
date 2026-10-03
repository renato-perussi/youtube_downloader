"""Testes dos formularios."""

from ytdownloader.forms import DownloadForm, SearchForm


def test_search_form_valid():
    form = SearchForm(data={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'})
    assert form.is_valid()


def test_search_form_invalid():
    form = SearchForm(data={'url': 'nao-e-url'})
    assert not form.is_valid()


def test_download_form_video_ok():
    form = DownloadForm(
        data={'url': 'https://www.youtube.com/watch?v=x', 'format_choice': 'mp4', 'quality': '720p'}
    )
    assert form.is_valid(), form.errors


def test_download_form_rejects_audio_quality_for_video():
    form = DownloadForm(
        data={
            'url': 'https://www.youtube.com/watch?v=x',
            'format_choice': 'mp4',
            'quality': '192kbps',
        }
    )
    assert not form.is_valid()
    assert 'quality' in form.errors


def test_download_form_rejects_video_quality_for_audio():
    form = DownloadForm(
        data={'url': 'https://www.youtube.com/watch?v=x', 'format_choice': 'mp3', 'quality': '720p'}
    )
    assert not form.is_valid()
    assert 'quality' in form.errors


def test_download_form_audio_ok():
    form = DownloadForm(
        data={
            'url': 'https://www.youtube.com/watch?v=x',
            'format_choice': 'mp3',
            'quality': '192kbps',
        }
    )
    assert form.is_valid(), form.errors
