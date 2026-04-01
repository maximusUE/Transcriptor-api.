FROM python:3.10-slim

WORKDIR /app

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY main.py .

# Exponer el puerto de Uvicorn
EXPOSE 8000

# Arrancar la API en producción
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
