"""Fixtures compartilhadas dos testes."""

import pytest
from django.contrib.auth.models import User

from ytdownloader.models import Download, Tenant


@pytest.fixture
def user(db):
    return User.objects.create_user(username='renato', password='senha123')


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username='maria', password='senha123')


@pytest.fixture
def tenant(user):
    return Tenant.resolve(user)


@pytest.fixture
def download(tenant, user):
    return Download.objects.create(
        tenant=tenant,
        user=user,
        url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        title='Video teste',
        format_choice='mp4',
        quality='720p',
        status='completed',
        progress=100,
    )
