"""Modelo Tenant (um por usuario)."""

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.utils.text import slugify


class Tenant(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant',
        verbose_name='Usuário',
    )
    slug = models.SlugField(max_length=50, unique=True, verbose_name='Slug')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return self.slug

    @classmethod
    def _unique_slug(cls, user, base_slug):
        candidate = base_slug[:50] or f'user-{user.pk}'
        suffix = 1
        while cls.objects.filter(slug=candidate).exclude(user=user).exists():
            suffix_str = f'-{suffix}'
            candidate = f'{base_slug[: 50 - len(suffix_str)]}{suffix_str}'
            suffix += 1
        return candidate

    @classmethod
    def resolve(cls, user):
        """Retorna o tenant do usuario, criando se necessario."""
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            pass
        base_slug = slugify(user.username)[:50] or f'user-{user.pk}'
        for _ in range(3):
            try:
                with transaction.atomic():
                    return cls.objects.create(user=user, slug=cls._unique_slug(user, base_slug))
            except IntegrityError:
                continue
        return cls.objects.get(user=user)
