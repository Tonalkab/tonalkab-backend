FROM python:3.11-slim

WORKDIR /app

# Copiamos primero el requirements para aprovechar la cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ahora copiamos TODO el código (no solo la carpeta app)
COPY . .

# Le decimos a Python que reconozca la carpeta actual como un módulo
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]