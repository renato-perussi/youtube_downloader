"""Excecoes de dominio da aplicacao."""

import re

_SENSITIVE_PATTERN = re.compile(
    r'(sig|ip|expire|key|token|signature)\s*=|https?://\S+|googlevideo|/videoplayback',
    re.IGNORECASE,
)


class DownloadServiceError(RuntimeError):
    """Erro amigavel de download exibido ao usuario."""


FRIENDLY_403_MESSAGE = 'YouTube recusou o download (403). Tente outro formato/qualidade.'

GENERIC_DOWNLOAD_ERROR = 'Falha no download. Tente outro formato/qualidade.'


def safe_error_message(detail):
    """Mapeia excecao bruta para mensagem segura ao usuario."""
    if not detail:
        return GENERIC_DOWNLOAD_ERROR
    lowered = detail.lower()
    if '403' in detail or 'forbidden' in lowered:
        return FRIENDLY_403_MESSAGE
    if _SENSITIVE_PATTERN.search(detail):
        return GENERIC_DOWNLOAD_ERROR
    return detail[:500]
