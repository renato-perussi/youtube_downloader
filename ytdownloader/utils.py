import os

import yt_dlp


def format_file_size(size_bytes):
    if not size_bytes:
        return None
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f'{size_bytes:.1f} {unit}'
        size_bytes /= 1024
    return f'{size_bytes:.1f} TB'


def _extract_raw_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'playlist_items': '1',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def _format_info(info, url):
    duration = info.get('duration')
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

    upload_date = info.get('upload_date')
    if upload_date and len(upload_date) == 8:
        upload_date_formatted = (
            f'{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[:4]}'
        )
    else:
        upload_date_formatted = ''

    view_count = info.get('view_count')
    view_count_formatted = f'{view_count:,}' if view_count is not None else '0'

    return {
        'title': info.get('title'),
        'thumbnail': info.get('thumbnail'),
        'duration_formatted': duration_formatted,
        'view_count_formatted': view_count_formatted,
        'channel': info.get('channel')
        or info.get('uploader')
        or 'Desconhecido',
        'upload_date_formatted': upload_date_formatted,
        'url': url,
    }


def get_video_info(url):
    raw = _extract_raw_info(url)
    return _format_info(raw, url)


def download_video(
    url, format_choice, quality, download_dir, progress_callback=None
):
    os.makedirs(download_dir, exist_ok=True)

    is_audio = format_choice in ('mp3', 'wav', 'flac')
    is_hd = quality in ('1080p', '720p')

    outtmpl = os.path.join(download_dir, '%(title)s.%(ext)s')

    ydl_opts = {
        'outtmpl': outtmpl,
        'restrictfilenames': True,
        'windowsfilenames': False,
    }

    if progress_callback:
        ydl_opts['progress_hooks'] = [progress_callback]

    if is_audio:
        ydl_opts.update(
            {
                'format': 'bestaudio/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': format_choice,
                    }
                ],
            }
        )
    else:
        format_string = f'bestvideo[height<={quality[:-1]}]+bestaudio/best[height<={quality[:-1]}]'
        ydl_opts['format'] = format_string
        ydl_opts['merge_output_format'] = format_choice

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'Unknown')
        filename = ydl.prepare_filename(info)

        if is_audio:
            filename = os.path.splitext(filename)[0] + f'.{format_choice}'

        if not os.path.exists(filename):
            base = os.path.splitext(filename)[0]
            alt_filename = f'{base}.{format_choice}'
            if os.path.exists(alt_filename):
                filename = alt_filename

        file_size = (
            os.path.getsize(filename) if os.path.exists(filename) else 0
        )
        final_filename = os.path.basename(filename)

        return {
            'title': title,
            'filename': final_filename,
            'file_size': file_size,
        }
