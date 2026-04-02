FROM python:3.10-slim

WORKDIR /app

# Instalar Node.js (requerido por yt-dlp para YouTube)
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos los archivos fuente
COPY . .

# Exponer el puerto de Uvicorn
EXPOSE 8000

# Arrancar la API en producción
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
