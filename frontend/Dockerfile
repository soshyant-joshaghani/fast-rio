FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/frontend
WORKDIR /app/frontend

ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=5000

COPY requirements.txt /app/requirements.txt
RUN python -m venv /app/.venv \
    && /app/.venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY frontend /app/frontend

EXPOSE 5000

# --public binds 0.0.0.0 (Traefik reaches the container). Behind Traefik only.
CMD ["rio", "run", "--port", "5000", "--release", "--public"]
