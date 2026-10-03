"""Formulario de busca por URL."""

from django import forms

from .validators import is_allowed_youtube_url

SEARCH_INPUT_CLASS = (
    'w-full px-4 py-2.5 bg-white/5 backdrop-blur-lg border border-white/10 rounded-l-xl '
    'focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent '
    'text-white placeholder-gray-400 transition-all duration-300'
)


class SearchForm(forms.Form):
    url = forms.URLField(
        label='Link do YouTube',
        widget=forms.URLInput(
            attrs={
                'class': SEARCH_INPUT_CLASS,
                'placeholder': 'https://www.youtube.com/watch?v=...',
            }
        ),
    )

    def clean_url(self):
        url = self.cleaned_data.get('url') or ''
        if not is_allowed_youtube_url(url):
            raise forms.ValidationError('Informe um link valido do YouTube.')
        return url
