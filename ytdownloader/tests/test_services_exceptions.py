"""Testes das excecoes e mensagens seguras."""

from ytdownloader.services.exceptions import GENERIC_DOWNLOAD_ERROR, safe_error_message


def test_safe_message_empty():
    assert safe_error_message('') == GENERIC_DOWNLOAD_ERROR
    assert safe_error_message(None) == GENERIC_DOWNLOAD_ERROR


def test_safe_message_403():
    assert '403' in safe_error_message('HTTP 403 Forbidden')


def test_safe_message_hides_signed_url():
    leaked = 'https://googlevideo.com/videoplayback?sig=abc&ip=1.2.3.4'
    assert safe_error_message(leaked) == GENERIC_DOWNLOAD_ERROR


def test_safe_message_passthrough():
    assert safe_error_message('Video indisponivel') == 'Video indisponivel'
