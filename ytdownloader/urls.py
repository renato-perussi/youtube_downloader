from django.urls import path

from . import views

urlpatterns = [
    path('<slug:slug>/', views.DownloadCreateView.as_view(), name='home'),
    path(
        '<slug:slug>/search/',
        views.SearchResultView.as_view(),
        name='search_result',
    ),
    path(
        '<slug:slug>/history/',
        views.DownloadHistoryView.as_view(),
        name='history',
    ),
    path(
        '<slug:slug>/detail/<int:pk>/',
        views.DownloadDetailView.as_view(),
        name='detail',
    ),
    path(
        '<slug:slug>/delete/<int:pk>/',
        views.DownloadDeleteView.as_view(),
        name='delete',
    ),
    path(
        '<slug:slug>/download/<int:pk>/',
        views.serve_download,
        name='serve_download',
    ),
    path(
        '<slug:slug>/progress/<int:pk>/',
        views.DownloadProgressView.as_view(),
        name='download_progress',
    ),
    path(
        '<slug:slug>/progress/<int:pk>/json/',
        views.download_progress_json,
        name='download_progress_json',
    ),
    path('<slug:slug>/download-all/', views.download_all, name='download_all'),
    path(
        '<slug:slug>/delete-all/',
        views.DownloadDeleteAllView.as_view(),
        name='delete_all',
    ),
]
