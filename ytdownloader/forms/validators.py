"""Validadores de URL do YouTube (anti-SSRF)."""

from ytdownloader.validators import YOUTUBE_HOSTS, is_allowed_youtube_url

__all__ = ['YOUTUBE_HOSTS', 'is_allowed_youtube_url']
