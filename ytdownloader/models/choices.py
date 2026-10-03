"""Choices compartilhados do dominio de downloads."""

from django.db import models


class DownloadFormat(models.TextChoices):
    MP4 = 'mp4', 'MP4'
    WEBM = 'webm', 'WebM'
    MP3 = 'mp3', 'MP3'
    WAV = 'wav', 'WAV'
    FLAC = 'flac', 'FLAC'


class DownloadQuality(models.TextChoices):
    QUALITY_1080P = '1080p', '1080p'
    QUALITY_720P = '720p', '720p'
    QUALITY_480P = '480p', '480p'
    QUALITY_360P = '360p', '360p'
    QUALITY_320KBPS = '320kbps', '320kbps'
    QUALITY_192KBPS = '192kbps', '192kbps'
    QUALITY_128KBPS = '128kbps', '128kbps'
    QUALITY_64KBPS = '64kbps', '64kbps'


class DownloadStatus(models.TextChoices):
    PENDING = 'pending', 'Pendente'
    PROCESSING = 'processing', 'Processando'
    COMPLETED = 'completed', 'Concluído'
    FAILED = 'failed', 'Falhou'


VIDEO_FORMATS = frozenset({DownloadFormat.MP4, DownloadFormat.WEBM})

AUDIO_FORMATS = frozenset({DownloadFormat.MP3, DownloadFormat.WAV, DownloadFormat.FLAC})
