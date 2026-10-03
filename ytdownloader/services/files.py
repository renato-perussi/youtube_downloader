"""Utilitarios de arquivo e midia."""

import io
import os
import zipfile

MAX_ZIP_FILES = 100
MAX_ZIP_TOTAL_BYTES = 500 * 1024 * 1024


def format_file_size(size_bytes):
    """Formata bytes em representacao legivel. Retorna None se vazio."""
    if not size_bytes:
        return None
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


def build_zip_buffer(downloads):
    """Monta um ZIP em memoria com os arquivos concluidos."""
    buffer = io.BytesIO()
    total = 0
    count = 0
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for download in downloads[:MAX_ZIP_FILES]:
            if not download.file:
                continue
            path = download.file.path
            if os.path.isfile(path):
                size = os.path.getsize(path)
                if total + size > MAX_ZIP_TOTAL_BYTES:
                    break
                zf.write(path, os.path.basename(download.file.name))
                total += size
                count += 1
    buffer.seek(0)
    return buffer
