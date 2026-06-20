FROM python:3.11-slim

WORKDIR /app

# Copiar requirements.txt primero (mejor para cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la carpeta 'app' dentro de /app (resultará en /app/app/...)
COPY ./app ./app

# Exponer el puerto que usará Cloud Run (por defecto 8080)
EXPOSE 8080

# Ejecutar uvicorn apuntando al módulo 'app.main'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]