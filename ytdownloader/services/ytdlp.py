"""Camada de integracao com o yt-dlp.

Centraliza opcoes base do YoutubeDL:
- runtime JS Node habilitado;
- multiplos player_client com fallback em caso de 403;
- retries e timeout robustos;
- erros convertidos em mensagens amigaveis.
"""

import logging
import os

import yt_dlp
from yt_dlp.utils import DownloadError

from ytdownloader.validators import is_allowed_youtube_url

from .exceptions import FRIENDLY_403_MESSAGE, DownloadServiceError, safe_error_message

logger = logging.getLogger(__name__)

DEFAULT_PLAYER_CLIENTS = ['default', 'web_embedded', 'ios', 'android']
FALLBACK_PLAYER_CLIENTS = ['default', 'web', 'ios', 'android']

MAX_VIDEO_DURATION_SECONDS = 2 * 60 * 60

CHROME_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/126.0.0.0 Safari/537.36'
)

AUDIO_FORMATS = frozenset({'mp3', 'wav', 'flac'})


def base_ydl_opts(js_runtime='node', player_clients=None):
    """Retorna opcoes base do yt-dlp."""
    clients = list(player_clients) if player_clients is not None else list(DEFAULT_PLAYER_CLIENTS)
    opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'playlist_items': 1,
        'extractor_args': {'youtube': {'player_client': clients}},
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
        'socket_timeout': 30,
        'user_agent': CHROME_UA,
    }
    if js_runtime:
        opts['js_runtimes'] = {js_runtime: {}}
    return opts


def extract_raw_info(url):
    """Extrai metadados brutos sem baixar."""
    ydl_opts = base_ydl_opts(js_runtime='node')
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def format_video_info(info, url):
    """Normaliza o dicionario bruto do yt-dlp para a sessao/UI."""
    duration = info.get('duration') or 0
    if duration:
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        if hours:
            duration_formatted = f'{hours}:{minutes:02d}:{seconds:02d}'
        else:
            duration_formatted = f'{minutes}:{seconds:02d}'
    else:
        duration_formatted = '00:00'

    upload_date = info.get('upload_date') or ''
    if len(upload_date) == 8:
        upload_date_formatted = f'{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[:4]}'
    else:
        upload_date_formatted = ''

    view_count = info.get('view_count')
    view_count_formatted = f'{view_count:,}' if view_count is not None else '0'

    return {
        'title': info.get('title'),
        'thumbnail': info.get('thumbnail'),
        'duration_formatted': duration_formatted,
        'duration_seconds': duration,
        'view_count_formatted': view_count_formatted,
        'channel': info.get('channel') or info.get('uploader') or 'Desconhecido',
        'upload_date_formatted': upload_date_formatted,
        'url': url,
    }


def get_video_info(url):
    """Busca e formata infos do video. Levanta DownloadServiceError em falha."""
    if not is_allowed_youtube_url(url):
        raise DownloadServiceError('Informe um link valido do YouTube.')
    try:
        raw = extract_raw_info(url)
    except Exception as exc:
        logger.warning('Falha ao extrair info de video: %s', safe_error_message(str(exc)))
        raise DownloadServiceError('Nao foi possivel ler este link. Confira a URL.') from exc
    if raw.get('is_live') or raw.get('live_status') in {'is_live', 'is_upcoming'}:
        raise DownloadServiceError('Transmissoes ao vivo nao sao suportadas.')
    formatted = format_video_info(raw, url)
    duration = formatted.get('duration_seconds') or 0
    if duration > MAX_VIDEO_DURATION_SECONDS:
        raise DownloadServiceError('Video muito longo (limite de 2 horas).')
    return formatted


def is_forbidden_error(exc):
    """Retorna True se a excecao indica HTTP 403/Forbidden."""
    msg = str(exc)
    return '403' in msg or 'forbidden' in msg.lower()


def build_ydl_opts(
    format_choice,
    quality,
    download_dir,
    progress_callback,
    player_clients,
    generic_fallback=False,
    download_id=None,
):
    """Monta opcoes de download mesclando base + formato."""
    opts = base_ydl_opts(js_runtime='node', player_clients=player_clients)
    template = (
        f'{download_id}_%(title)s.%(ext)s' if download_id is not None else '%(title)s.%(ext)s'
    )
    opts.update(
        {
            'outtmpl': os.path.join(download_dir, template),
            'restrictfilenames': True,
            'windowsfilenames': False,
        }
    )
    if progress_callback:
        opts['progress_hooks'] = [progress_callback]

    if format_choice in AUDIO_FORMATS:
        opts.update(
            {
                'format': 'bestaudio/best',
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': format_choice},
                ],
            }
        )
    elif generic_fallback:
        opts['format'] = 'bestvideo+bestaudio/best'
        opts['merge_output_format'] = format_choice
    else:
        height = quality[:-1] if quality.endswith('p') else quality
        opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
        opts['merge_output_format'] = format_choice
    return opts


def execute_download(ydl_opts, url, format_choice):
    """Executa o download uma vez e resolve nome/tamanho do arquivo."""
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'Unknown')
        filename = ydl.prepare_filename(info)

        if format_choice in AUDIO_FORMATS:
            filename = os.path.splitext(filename)[0] + f'.{format_choice}'

        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            alt_filename = f'{base}.{format_choice}'
            if os.path.exists(alt_filename):
                filename = alt_filename

        file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
        return {'title': title, 'filename': os.path.basename(filename), 'file_size': file_size}


def download_video(
    url, format_choice, quality, download_dir, progress_callback=None, download_id=None
):
    """Baixa com retry de fallback. Retorna dict com title/filename/file_size."""
    if not is_allowed_youtube_url(url):
        raise DownloadServiceError('Informe um link valido do YouTube.')
    os.makedirs(download_dir, exist_ok=True)

    primary_opts = build_ydl_opts(
        format_choice,
        quality,
        download_dir,
        progress_callback,
        player_clients=DEFAULT_PLAYER_CLIENTS,
        generic_fallback=False,
        download_id=download_id,
    )
    try:
        return execute_download(primary_opts, url, format_choice)
    except DownloadError as exc:
        if not is_forbidden_error(exc):
            logger.warning('Download falhou (sem retry): %s', safe_error_message(str(exc)))
            raise DownloadServiceError('Falha no download. Tente outro formato/qualidade.') from exc
        logger.warning('Tentativa primaria 403, tentando fallback')

    fallback_opts = build_ydl_opts(
        format_choice,
        quality,
        download_dir,
        progress_callback,
        player_clients=FALLBACK_PLAYER_CLIENTS,
        generic_fallback=True,
        download_id=download_id,
    )
    try:
        return execute_download(fallback_opts, url, format_choice)
    except Exception as exc:
        logger.warning('Fallback de download falhou: %s', safe_error_message(str(exc)))
        raise DownloadServiceError(FRIENDLY_403_MESSAGE) from exc
