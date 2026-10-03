"""Admin do ytdownloader."""

from django.contrib import admin

from .models import Download, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['slug', 'user', 'is_active', 'created_at']
    search_fields = ['slug', 'user__username']
    list_filter = ['is_active']


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'tenant',
        'user',
        'format_choice',
        'quality',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'format_choice', 'quality', 'created_at']
    search_fields = ['title', 'url', 'user__username', 'tenant__slug']
    readonly_fields = ['file_size', 'created_at']
