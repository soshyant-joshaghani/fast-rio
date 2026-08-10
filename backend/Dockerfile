FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend
WORKDIR /app/

ENV PATH="/app/.venv/bin:$PATH"

COPY requirements.txt /app/requirements.txt
RUN python -m venv /app/.venv && pip install --no-cache-dir -r requirements.txt

COPY backend/scripts /app/backend/scripts
RUN sed -i 's/\r$//' /app/backend/scripts/*.sh && chmod +x /app/backend/scripts/*.sh

COPY backend/alembic.ini /app/backend/
COPY backend/app /app/backend/app

WORKDIR /app/backend/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
