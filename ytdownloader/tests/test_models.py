"""Testes dos modelos Tenant e Download."""

import pytest

from ytdownloader.models import Download, Tenant


@pytest.mark.django_db
def test_tenant_resolve_creates_once(user):
    first = Tenant.resolve(user)
    second = Tenant.resolve(user)
    assert first.pk == second.pk
    assert first.slug == 'renato'
    assert Tenant.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_tenant_str(tenant):
    assert str(tenant) == tenant.slug


@pytest.mark.django_db
def test_download_str(download):
    assert str(download) == 'Video teste (mp4)'


@pytest.mark.django_db
def test_download_queryset_for_tenant(tenant, other_user, download):
    other_tenant = Tenant.resolve(other_user)
    assert list(Download.objects.for_tenant(tenant)) == [download]
    assert list(Download.objects.for_tenant(other_tenant)) == []


@pytest.mark.django_db
def test_download_queryset_search(download):
    qs = Download.objects.all().search('video')
    assert download in qs
    qs_empty = Download.objects.all().search('inexistente')
    assert download not in qs_empty


@pytest.mark.django_db
def test_download_completed_filter(tenant, user):
    pending = Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=abc',
        title='Pendente',
        format_choice='mp4',
        quality='720p',
        status='processing',
    )
    completed = Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=def',
        title='OK',
        format_choice='mp3',
        quality='192kbps',
        status='completed',
    )
    completed.file.name = 'downloads/ok.mp3'
    completed.save()
    assert pending not in Download.objects.completed()
    assert completed in Download.objects.completed()
