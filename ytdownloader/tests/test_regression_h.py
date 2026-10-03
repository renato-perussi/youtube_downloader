"""Regressao H01-H03 e defesa em profundidade."""

from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from ytdownloader.models import Download, Tenant
from ytdownloader.services.downloads import _DOWNLOAD_SEMAPHORE
from ytdownloader.services.exceptions import DownloadServiceError
from ytdownloader.services.ytdlp import build_ydl_opts, download_video, get_video_info


@pytest.mark.django_db
def test_tenant_slug_collision_suffix():
    user_a = User.objects.create_user(username='User.Name', password='x')
    tenant_a = Tenant.resolve(user_a)
    user_b = User.objects.create_user(username='UserName', password='x')
    tenant_b = Tenant.resolve(user_b)
    assert tenant_a.slug != tenant_b.slug
    assert Tenant.objects.count() == 2


@pytest.mark.django_db
def test_view_semaphore_full_returns_200(client, user, tenant):
    client.force_login(user)
    session = client.session
    session['download_video_info'] = {
        'title': 'T',
        'url': 'https://www.youtube.com/watch?v=aaa',
    }
    session.save()
    assert _DOWNLOAD_SEMAPHORE.acquire(blocking=False)
    assert _DOWNLOAD_SEMAPHORE.acquire(blocking=False)
    try:
        with patch(
            'ytdownloader.views.search.get_video_info',
            return_value={'title': 'T', 'url': 'https://www.youtube.com/watch?v=aaa'},
        ):
            response = client.post(
                reverse('search_result', kwargs={'slug': tenant.slug}),
                {
                    'action': 'download',
                    'url': 'https://www.youtube.com/watch?v=aaa',
                    'format_choice': 'mp4',
                    'quality': '720p',
                },
            )
        assert response.status_code == 200
        assert 'simultaneos' in str(response.context['download_form'].errors).lower()
    finally:
        _DOWNLOAD_SEMAPHORE.release()
        _DOWNLOAD_SEMAPHORE.release()


@pytest.mark.django_db
def test_direct_download_long_rejected_without_session(client, user, tenant):
    client.force_login(user)
    before = Download.objects.count()
    with patch(
        'ytdownloader.views.search.get_video_info',
        side_effect=DownloadServiceError('Video muito longo (limite de 2 horas).'),
    ):
        response = client.post(
            reverse('search_result', kwargs={'slug': tenant.slug}),
            {
                'action': 'download',
                'url': 'https://www.youtube.com/watch?v=longvideo',
                'format_choice': 'mp4',
                'quality': '720p',
            },
        )
    assert response.status_code == 200
    assert Download.objects.count() == before


def test_outtmpl_unique_per_job(tmp_path):
    opts_a = build_ydl_opts('mp4', '720p', str(tmp_path), None, ['default'], download_id=1)
    opts_b = build_ydl_opts('mp4', '720p', str(tmp_path), None, ['default'], download_id=2)
    assert opts_a['outtmpl'] != opts_b['outtmpl']
    assert '1_' in opts_a['outtmpl']
    assert '2_' in opts_b['outtmpl']


def test_service_layer_rejects_non_youtube():
    with pytest.raises(DownloadServiceError):
        get_video_info('https://example.com/video')
    with pytest.raises(DownloadServiceError):
        download_video('https://example.com/video', 'mp4', '720p', '/tmp')


@pytest.mark.django_db
def test_mixins_anonymous_redirects_to_login(client):
    response = client.get('/qualquer-slug/')
    assert response.status_code == 302
    assert 'login' in response.url


@pytest.mark.django_db
def test_mixins_preserves_querystring(client, user, tenant):
    client.force_login(user)
    response = client.get('/outro-slug/history/?q=teste&page=2')
    assert response.status_code == 302
    assert 'q=teste' in response.url
    assert tenant.slug in response.url
