#!/bin/sh
set -e

echo 'Aplicando migracoes...'
python manage.py migrate --noinput

echo 'Coletando estaticos...'
python manage.py collectstatic --noinput || true

echo 'Iniciando aplicacao...'
exec "$@"
