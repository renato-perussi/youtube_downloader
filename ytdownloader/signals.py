"""Signals do app ytdownloader."""

from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Download, Tenant


@receiver(post_save, sender=User)
def create_tenant(sender, instance, created, **kwargs):
    if created:
        Tenant.resolve(instance)


@receiver(post_delete, sender=Download)
def delete_download_file(sender, instance, **kwargs):
    if instance.file and instance.file.storage.exists(instance.file.name):
        instance.file.storage.delete(instance.file.name)
