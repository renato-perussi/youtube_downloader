"""Testes das views CBV e isolamento multi-tenant."""

from unittest.mock import patch

import pytest
from django.urls import reverse

from ytdownloader.models import Download, Tenant


@pytest.mark.django_db
def test_root_redirect_anonymous(client):
    response = client.get(reverse('root'))
    assert response.status_code == 302
    assert 'login' in response.url


@pytest.mark.django_db
def test_root_redirect_authenticated(client, user):
    client.force_login(user)
    response = client.get(reverse('root'))
    tenant = Tenant.resolve(user)
    assert response.url == f'/{tenant.slug}/'


@pytest.mark.django_db
def test_home_requires_login(client, tenant):
    response = client.get(reverse('home', kwargs={'slug': tenant.slug}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_home_renders_search(client, user, tenant):
    client.force_login(user)
    response = client.get(reverse('home', kwargs={'slug': tenant.slug}))
    assert response.status_code == 200
    assert 'search_form' in response.context


@pytest.mark.django_db
def test_tenant_slug_mismatch_redirects(client, user, tenant):
    client.force_login(user)
    response = client.get(reverse('home', kwargs={'slug': 'outro-slug'}))
    assert response.status_code == 302
    assert tenant.slug in response.url


@pytest.mark.django_db
def test_search_post_fetch_and_redirect(client, user, tenant):
    client.force_login(user)
    fake_info = {'title': 'T', 'url': 'https://youtu.be/x'}
    with patch('ytdownloader.views.mixins.get_video_info', return_value=fake_info):
        response = client.post(
            reverse('home', kwargs={'slug': tenant.slug}),
            {'action': 'search', 'url': 'https://youtu.be/x'},
        )
    assert response.status_code == 302
    assert response.url.endswith(f'/{tenant.slug}/search/')


@pytest.mark.django_db
def test_search_result_requires_session(client, user, tenant):
    client.force_login(user)
    response = client.get(reverse('search_result', kwargs={'slug': tenant.slug}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_download_creation_starts_thread(client, user, tenant):
    client.force_login(user)
    session = client.session
    session['download_video_info'] = {'title': 'T', 'url': 'https://youtu.be/x'}
    session.save()
    with (
        patch('ytdownloader.views.search.create_and_start_download') as mock_create,
        patch(
            'ytdownloader.views.search.get_video_info',
            return_value={'title': 'T', 'url': 'https://youtu.be/x'},
        ),
    ):
        fake = Download.objects.create(
            tenant=tenant,
            user=user,
            url='https://youtu.be/x',
            title='Processando...',
            format_choice='mp4',
            quality='720p',
            status='processing',
        )
        mock_create.return_value = fake
        response = client.post(
            reverse('search_result', kwargs={'slug': tenant.slug}),
            {
                'action': 'download',
                'url': 'https://youtu.be/x',
                'format_choice': 'mp4',
                'quality': '720p',
            },
        )
    assert response.status_code == 302
    assert str(fake.pk) in response.url


@pytest.mark.django_db
def test_history_isolated_by_tenant(client, user, other_user, tenant, download):
    other_tenant = Tenant.resolve(other_user)
    Download.objects.create(
        tenant=other_tenant,
        user=other_user,
        url='https://youtu.be/y',
        title='Outro',
        format_choice='mp3',
        quality='128kbps',
        status='completed',
    )
    client.force_login(user)
    response = client.get(reverse('history', kwargs={'slug': tenant.slug}))
    titles = [d.title for d in response.context['downloads']]
    assert 'Video teste' in titles
    assert 'Outro' not in titles


@pytest.mark.django_db
def test_progress_json_view(client, user, tenant, download):
    client.force_login(user)
    url = reverse('download_progress_json', kwargs={'slug': tenant.slug, 'pk': download.pk})
    response = client.get(url)
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'completed'
    assert payload['progress'] == 100


@pytest.mark.django_db
def test_progress_json_other_user_forbidden(client, other_user, tenant, download):
    client.force_login(other_user)
    url = reverse('download_progress_json', kwargs={'slug': tenant.slug, 'pk': download.pk})
    response = client.get(url)
    assert response.status_code == 404
