"""Healthcheck com verificacao de banco."""

from django.db import connections
from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    """Retorna 200 apenas se o banco responder."""

    def get(self, request):
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
        except Exception:
            return JsonResponse({'status': 'unhealthy'}, status=503)
        return JsonResponse({'status': 'ok'})
