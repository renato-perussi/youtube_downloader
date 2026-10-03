"""Exports das views (todas Class-Based)."""

from .auth import LoginRedirectView, RegisterView, RootRedirectView
from .files import DownloadAllView, ServeDownloadView
from .health import HealthCheckView
from .history import (
    DownloadDeleteAllView,
    DownloadDeleteView,
    DownloadDetailView,
    DownloadHistoryView,
)
from .home import DownloadCreateView
from .mixins import SearchMixin, TenantAwareMixin
from .progress import DownloadProgressJsonView, DownloadProgressView
from .search import SearchResultView

__all__ = [
    'DownloadAllView',
    'DownloadCreateView',
    'DownloadDeleteAllView',
    'DownloadDeleteView',
    'DownloadDetailView',
    'DownloadHistoryView',
    'DownloadProgressJsonView',
    'DownloadProgressView',
    'HealthCheckView',
    'LoginRedirectView',
    'RegisterView',
    'RootRedirectView',
    'SearchMixin',
    'SearchResultView',
    'ServeDownloadView',
    'TenantAwareMixin',
]
