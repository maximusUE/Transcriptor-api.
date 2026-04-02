FROM python:3.10-slim

WORKDIR /app

# Instalar Node.js y crear el enlace "node" que busca yt-dlp
RUN apt-get update && apt-get install -y nodejs npm && \
    ln -sf /usr/bin/nodejs /usr/local/bin/node && \
    rm -rf /var/lib/apt/lists/*

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos los archivos
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
