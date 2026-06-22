#!/bin/sh
set -e

echo "Gerando as migrações..."
python manage.py makemigrations

echo "Aplicando as migrações no banco de dados..."
python manage.py migrate

echo "Iniciando o servidor..."
exec "$@"
