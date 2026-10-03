"""Modelo Download com querysets especializados por tenant."""

from django.conf import settings
from django.db import models

from .choices import DownloadFormat, DownloadQuality, DownloadStatus


class DownloadQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        return self.filter(tenant=tenant)

    def completed(self):
        return self.filter(status=DownloadStatus.COMPLETED, file__isnull=False)

    def search(self, term):
        term = (term or '').strip()
        if not term:
            return self
        return self.filter(
            models.Q(title__icontains=term) | models.Q(format_choice__icontains=term)
        )


class Download(models.Model):
    tenant = models.ForeignKey(
        'ytdownloader.Tenant',
        on_delete=models.CASCADE,
        related_name='downloads',
        verbose_name='Tenant',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Usuário',
    )
    url = models.URLField('URL do YouTube')
    title = models.CharField('Título', max_length=200)
    format_choice = models.CharField('Formato', max_length=10, choices=DownloadFormat.choices)
    quality = models.CharField('Qualidade', max_length=10, choices=DownloadQuality.choices)
    file = models.FileField('Arquivo', upload_to='downloads/', null=True, blank=True)
    file_size = models.BigIntegerField('Tamanho do arquivo', null=True, blank=True)
    progress = models.IntegerField('Progresso', default=0)
    status = models.CharField(
        'Status',
        max_length=20,
        choices=DownloadStatus.choices,
        default=DownloadStatus.PENDING,
    )
    error_message = models.TextField('Mensagem de erro', null=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    objects = DownloadQuerySet.as_manager()

    class Meta:
        verbose_name = 'Download'
        verbose_name_plural = 'Downloads'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.format_choice})'

    @property
    def is_completed(self):
        return self.status == DownloadStatus.COMPLETED

    @property
    def is_failed(self):
        return self.status == DownloadStatus.FAILED
