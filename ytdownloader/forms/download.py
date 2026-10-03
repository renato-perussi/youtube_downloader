"""Formulario de selecao de formato/qualidade."""

from django import forms

from ytdownloader.models.choices import (
    AUDIO_FORMATS,
    VIDEO_FORMATS,
    DownloadFormat,
    DownloadQuality,
)

from .validators import is_allowed_youtube_url

SELECT_CLASS = (
    'w-full px-4 py-2.5 bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl '
    'focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent '
    'text-white transition-all duration-300'
)


class DownloadForm(forms.Form):
    url = forms.URLField(widget=forms.HiddenInput())

    format_choice = forms.ChoiceField(
        label='Formato',
        choices=DownloadFormat.choices,
        widget=forms.Select(attrs={'class': SELECT_CLASS, 'onchange': 'updateQualities()'}),
    )

    quality = forms.ChoiceField(
        label='Qualidade',
        choices=DownloadQuality.choices,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
    )

    def clean_url(self):
        url = self.cleaned_data.get('url') or ''
        if not is_allowed_youtube_url(url):
            raise forms.ValidationError('Informe um link valido do YouTube.')
        return url

    def clean_quality(self):
        format_choice = self.cleaned_data.get('format_choice')
        value = self.cleaned_data.get('quality') or ''
        if not value:
            return value
        if format_choice in VIDEO_FORMATS and value.endswith('kbps'):
            raise forms.ValidationError('Qualidade de áudio não é válida para formato de vídeo.')
        if format_choice in AUDIO_FORMATS and value.endswith('p'):
            raise forms.ValidationError('Qualidade de vídeo não é válida para formato de áudio.')
        return value
