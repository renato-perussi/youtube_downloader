"""URLs raiz do projeto (todas CBV)."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from ytdownloader.views import HealthCheckView, LoginRedirectView, RegisterView, RootRedirectView

urlpatterns = [
    path('healthz/', HealthCheckView.as_view(), name='healthz'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('login_redirect/', LoginRedirectView.as_view(), name='login_redirect'),
    path('', RootRedirectView.as_view(), name='root'),
    path('', include('ytdownloader.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
