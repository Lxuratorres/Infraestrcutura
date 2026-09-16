FROM python:3.11-slim

LABEL maintainer="Didier Agamez" \
      description="Aplicación web mínima en Python con Flask - Ejercicio 1" \
      version="1.0"

ENV FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN useradd -m appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]