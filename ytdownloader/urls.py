"""URLs do app ytdownloader (100% CBV, prefixo por slug do tenant)."""

from django.urls import path

from .views import (
    DownloadAllView,
    DownloadCreateView,
    DownloadDeleteAllView,
    DownloadDeleteView,
    DownloadDetailView,
    DownloadHistoryView,
    DownloadProgressJsonView,
    DownloadProgressView,
    SearchResultView,
    ServeDownloadView,
)

urlpatterns = [
    path('<slug:slug>/', DownloadCreateView.as_view(), name='home'),
    path('<slug:slug>/search/', SearchResultView.as_view(), name='search_result'),
    path('<slug:slug>/history/', DownloadHistoryView.as_view(), name='history'),
    path('<slug:slug>/detail/<int:pk>/', DownloadDetailView.as_view(), name='detail'),
    path('<slug:slug>/delete/<int:pk>/', DownloadDeleteView.as_view(), name='delete'),
    path('<slug:slug>/download/<int:pk>/', ServeDownloadView.as_view(), name='serve_download'),
    path(
        '<slug:slug>/progress/<int:pk>/', DownloadProgressView.as_view(), name='download_progress'
    ),
    path(
        '<slug:slug>/progress/<int:pk>/json/',
        DownloadProgressJsonView.as_view(),
        name='download_progress_json',
    ),
    path('<slug:slug>/download-all/', DownloadAllView.as_view(), name='download_all'),
    path('<slug:slug>/delete-all/', DownloadDeleteAllView.as_view(), name='delete_all'),
]
