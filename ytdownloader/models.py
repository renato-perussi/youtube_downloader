from django.conf import settings
from django.db import models


class Tenant(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant',
        verbose_name='Usuário',
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Slug',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    @classmethod
    def resolve(cls, user):
        tenant, _ = cls.objects.get_or_create(
            user=user,
            defaults={'slug': user.username[:50]},
        )
        return tenant

    def __str__(self):
        return self.slug


class Download(models.Model):
    class FormatChoices(models.TextChoices):
        MP4 = 'mp4', 'MP4'
        WEBM = 'webm', 'WebM'
        MP3 = 'mp3', 'MP3'
        WAV = 'wav', 'WAV'
        FLAC = 'flac', 'FLAC'

    class QualityChoices(models.TextChoices):
        QUALITY_1080P = '1080p', '1080p'
        QUALITY_720P = '720p', '720p'
        QUALITY_480P = '480p', '480p'
        QUALITY_360P = '360p', '360p'
        QUALITY_320KBPS = '320kbps', '320kbps'
        QUALITY_192KBPS = '192kbps', '192kbps'
        QUALITY_128KBPS = '128kbps', '128kbps'
        QUALITY_64KBPS = '64kbps', '64kbps'

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PROCESSING = 'processing', 'Processando'
        COMPLETED = 'completed', 'Concluído'
        FAILED = 'failed', 'Falhou'

    tenant = models.ForeignKey(
        Tenant,
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
    format_choice = models.CharField(
        'Formato', max_length=10, choices=FormatChoices.choices
    )
    quality = models.CharField(
        'Qualidade', max_length=10, choices=QualityChoices.choices
    )
    file = models.FileField(
        'Arquivo', upload_to='downloads/', null=True, blank=True
    )
    file_size = models.BigIntegerField(
        'Tamanho do arquivo', null=True, blank=True
    )
    progress = models.IntegerField('Progresso', default=0)
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    error_message = models.TextField('Mensagem de erro', null=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Download'
        verbose_name_plural = 'Downloads'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.format_choice})'
