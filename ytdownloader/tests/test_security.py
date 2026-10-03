"""Testes de seguranca anti-SSRF e validacao YouTube."""

from ytdownloader.forms import DownloadForm, SearchForm


def test_search_rejects_metadata_ip():
    form = SearchForm(data={'url': 'http://169.254.169.254/latest/meta-data/'})
    assert not form.is_valid()


def test_search_rejects_non_youtube():
    form = SearchForm(data={'url': 'https://example.com/video'})
    assert not form.is_valid()


def test_search_rejects_ftp():
    form = SearchForm(data={'url': 'ftp://example.com/file'})
    assert not form.is_valid()


def test_search_accepts_youtu_be():
    form = SearchForm(data={'url': 'https://youtu.be/dQw4w9WgXcQ'})
    assert form.is_valid(), form.errors


def test_search_accepts_music_youtube():
    form = SearchForm(data={'url': 'https://music.youtube.com/watch?v=x'})
    assert form.is_valid(), form.errors


def test_download_rejects_non_youtube():
    form = DownloadForm(
        data={'url': 'https://example.com/x', 'format_choice': 'mp4', 'quality': '720p'}
    )
    assert not form.is_valid()
    assert 'url' in form.errors
