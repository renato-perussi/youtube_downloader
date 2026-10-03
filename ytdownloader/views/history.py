"""Historico e detalhe/exclusao de downloads."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DeleteView, DetailView, ListView, TemplateView

from ytdownloader.models import Download

from .mixins import TenantAwareMixin


class DownloadHistoryView(LoginRequiredMixin, TenantAwareMixin, ListView):
    model = Download
    template_name = 'ytdownloader/download_list.html'
    context_object_name = 'downloads'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.search(self.request.GET.get('q', ''))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['has_completed_downloads'] = (
            Download.objects.filter(tenant=self.request.tenant).completed().exists()
        )
        return context


class DownloadDetailView(LoginRequiredMixin, TenantAwareMixin, DetailView):
    model = Download
    template_name = 'ytdownloader/download_detail.html'
    context_object_name = 'download'


class DownloadDeleteView(LoginRequiredMixin, TenantAwareMixin, SuccessMessageMixin, DeleteView):
    model = Download
    template_name = 'ytdownloader/download_confirm_delete.html'
    success_message = 'Download excluído com sucesso.'

    def get_success_url(self):
        return reverse('history', args=[self.request.tenant.slug])


class DownloadDeleteAllView(LoginRequiredMixin, TenantAwareMixin, TemplateView):
    template_name = 'ytdownloader/confirm_delete_all.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total'] = Download.objects.filter(tenant=self.request.tenant).count()
        return context

    def post(self, request, *args, **kwargs):
        Download.objects.filter(tenant=request.tenant).delete()
        return redirect('history', slug=request.tenant.slug)
