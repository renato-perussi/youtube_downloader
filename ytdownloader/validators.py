"""Validador canonico de URLs YouTube (usado por forms e services)."""

from urllib.parse import urlparse

YOUTUBE_HOSTS = frozenset(
    {
        'youtube.com',
        'www.youtube.com',
        'm.youtube.com',
        'music.youtube.com',
        'youtu.be',
        'www.youtu.be',
        'youtube-nocookie.com',
        'www.youtube-nocookie.com',
    }
)


def is_allowed_youtube_url(url):
    """Retorna True apenas para http(s) em hosts oficiais do YouTube."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {'http', 'https'}:
        return False
    host = (parsed.hostname or '').lower()
    if not host or host in {'localhost'}:
        return False
    if host.startswith('127.') or host.startswith('10.') or host.startswith('192.168.'):
        return False
    if host == '169.254.169.254':
        return False
    return host in YOUTUBE_HOSTS
