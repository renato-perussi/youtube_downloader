"""Testes de arquivos, healthcheck e tenant slugify."""

import pytest
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.urls import reverse

from ytdownloader.models import Download, Tenant


@pytest.mark.django_db
def test_tenant_slugify_dotted_username():
    user = User.objects.create_user(username='john.doe', password='x')
    tenant = Tenant.resolve(user)
    assert tenant.slug == 'johndoe'
    assert '.' not in tenant.slug


@pytest.mark.django_db
def test_healthz_ok(client):
    response = client.get(reverse('healthz'))
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


@pytest.mark.django_db
def test_serve_download_200(client, user, tenant):
    download = Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=x',
        title='Demo',
        format_choice='mp4',
        quality='720p',
        status='completed',
    )
    download.file.save('demo-serve.mp4', ContentFile(b'hello'))
    try:
        client.force_login(user)
        url = reverse('serve_download', kwargs={'slug': tenant.slug, 'pk': download.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert b'hello' in b''.join(response.streaming_content)
    finally:
        download.file.delete(save=False)


@pytest.mark.django_db
def test_serve_download_cross_tenant_404(client, other_user, tenant, download):
    client.force_login(other_user)
    url = reverse('serve_download', kwargs={'slug': tenant.slug, 'pk': download.pk})
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_download_all_zip_only_completed(client, user, tenant):
    done = Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=a',
        title='Done',
        format_choice='mp4',
        quality='720p',
        status='completed',
    )
    done.file.save('done.zip.mp4', ContentFile(b'data'))
    Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=b',
        title='Pending',
        format_choice='mp4',
        quality='720p',
        status='processing',
    )
    try:
        client.force_login(user)
        url = reverse('download_all', kwargs={'slug': tenant.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/zip'
    finally:
        done.file.delete(save=False)


@pytest.mark.django_db
def test_delete_removes_object(client, user, tenant, download):
    client.force_login(user)
    url = reverse('delete', kwargs={'slug': tenant.slug, 'pk': download.pk})
    response = client.post(url)
    assert response.status_code == 302
    assert not Download.objects.filter(pk=download.pk).exists()


@pytest.mark.django_db
def test_session_url_mismatch_rejected(client, user, tenant):
    client.force_login(user)
    session = client.session
    session['download_video_info'] = {'title': 'T', 'url': 'https://www.youtube.com/watch?v=aaa'}
    session.save()
    response = client.post(
        reverse('search_result', kwargs={'slug': tenant.slug}),
        {
            'action': 'download',
            'url': 'https://www.youtube.com/watch?v=bbb',
            'format_choice': 'mp4',
            'quality': '720p',
        },
    )
    assert response.status_code == 200
    assert 'divergente' in str(response.context['download_form'].errors).lower()
