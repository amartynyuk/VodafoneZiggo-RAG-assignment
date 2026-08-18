FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Build context is the repo root so kb-store can be installed from packages/.
COPY packages/kb-store /packages/kb-store
COPY services/kb-builder/requirements.txt .
RUN pip install --no-cache-dir /packages/kb-store \
    && pip install --no-cache-dir -r requirements.txt

COPY services/kb-builder/app/ ./app/

ENV DATA_DIR=/app/data
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
