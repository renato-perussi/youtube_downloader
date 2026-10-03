"""Testes dos servicos de arquivo."""

from django.core.files.base import ContentFile

from ytdownloader.models import Download
from ytdownloader.services.files import build_zip_buffer, format_file_size


def test_format_file_size_none():
    assert format_file_size(None) is None
    assert format_file_size(0) is None


def test_format_file_size_units():
    assert format_file_size(512) == '512.0 B'
    assert format_file_size(2048) == '2.0 KB'
    assert format_file_size(1024 * 1024) == '1.0 MB'


def test_build_zip_buffer_empty():
    buffer = build_zip_buffer([])
    assert buffer.getvalue()[:2] == b'PK'


def test_build_zip_buffer_with_file(tmp_path, db, tenant, user):
    media_file = tmp_path / 'demo.mp4'
    media_file.write_bytes(b'hello')
    download = Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=x',
        title='Demo',
        format_choice='mp4',
        quality='720p',
        status='completed',
    )
    download.file.save('demo.mp4', ContentFile(b'hello'))
    try:
        buffer = build_zip_buffer([download])
        assert len(buffer.getvalue()) > 0
    finally:
        download.file.delete(save=False)
