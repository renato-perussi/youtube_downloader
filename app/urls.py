from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from ytdownloader.models import Tenant
from ytdownloader.views import RegisterView, login_redirect


def root_redirect(request):
    if request.user.is_authenticated:
        tenant = Tenant.resolve(request.user)
        return redirect('home', slug=tenant.slug)
    return redirect('login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('login_redirect/', login_redirect, name='login_redirect'),
    path('', root_redirect, name='root'),
    path('', include('ytdownloader.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
