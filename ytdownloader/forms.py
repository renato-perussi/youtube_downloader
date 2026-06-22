from django import forms

from .models import Download

VIDEO_FORMATS = {Download.FormatChoices.MP4, Download.FormatChoices.WEBM}
AUDIO_FORMATS = {
    Download.FormatChoices.MP3,
    Download.FormatChoices.WAV,
    Download.FormatChoices.FLAC,
}


class SearchForm(forms.Form):
    url = forms.URLField(
        label='Link do YouTube',
        widget=forms.URLInput(
            attrs={
                'class': 'w-full px-4 py-2.5 bg-white/5 backdrop-blur-lg border border-white/10 rounded-l-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent text-white placeholder-gray-400 transition-all duration-300',
                'placeholder': 'https://www.youtube.com/watch?v=...',
            }
        ),
    )


class DownloadForm(forms.Form):
    url = forms.URLField(widget=forms.HiddenInput())

    format_choice = forms.ChoiceField(
        label='Formato',
        choices=Download.FormatChoices.choices,
        widget=forms.Select(
            attrs={
                'class': 'w-full px-4 py-2.5 bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent text-white transition-all duration-300',
                'onchange': 'updateQualities()',
            }
        ),
    )

    quality = forms.ChoiceField(
        label='Qualidade',
        choices=Download.QualityChoices.choices,
        widget=forms.Select(
            attrs={
                'class': 'w-full px-4 py-2.5 bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent text-white transition-all duration-300',
            }
        ),
    )

    def clean_quality(self):
        format_choice = self.cleaned_data.get('format_choice')
        value = self.cleaned_data.get('quality')

        is_video = format_choice in VIDEO_FORMATS
        is_audio = format_choice in AUDIO_FORMATS

        if is_video and value.endswith('kbps'):
            raise forms.ValidationError(
                'Qualidade de áudio não é válida para formato de vídeo.'
            )

        if is_audio and value.endswith('p'):
            raise forms.ValidationError(
                'Qualidade de vídeo não é válida para formato de áudio.'
            )

        return value
