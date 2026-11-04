# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /srv
COPY app/ ./app/
RUN useradd --create-home --uid 10001 app
USER 10001

EXPOSE 8080
HEALTHCHECK --interval=2s --timeout=2s --start-period=3s --retries=10 \
  CMD python -c "import os,socket; s=socket.create_connection(('127.0.0.1', int(os.environ['PORT'])), 2); s.close()"

CMD ["python", "app/server.py"]
