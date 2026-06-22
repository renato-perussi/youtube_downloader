FROM python:3.12-slim

# Evita que o Python escreva arquivos .pyc no disco (equivalente a python -B)
ENV PYTHONDONTWRITEBYTECODE 1
# Evita que o Python faça buffer do stdout e stderr (equivalente a python -u)
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho no container
WORKDIR /app

# Instala o ffmpeg (dependência necessária para o yt-dlp)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do projeto
COPY . /app/

# Garante permissão de execução no script de inicialização
RUN chmod +x /app/entrypoint.sh

# Expõe a porta que será utilizada pela aplicação
EXPOSE 8000

# Define o script como inicializador padrão
ENTRYPOINT ["sh", "/app/entrypoint.sh"]

# Comando para inicializar a aplicação (executado pelo entrypoint)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
