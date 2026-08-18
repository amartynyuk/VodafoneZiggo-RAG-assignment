FROM python:3.12-slim

WORKDIR /app

# curl is used by Docker healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Build context is the repo root (see docker-compose.yml) so we can install
# the shared kb-store package alongside this service.
COPY packages/kb-store /packages/kb-store
COPY services/ai-assistant/requirements.txt .
RUN pip install --no-cache-dir /packages/kb-store \
    && pip install --no-cache-dir -r requirements.txt

# Bake BERT security weights into the image (HF_HOME is also used at runtime).
ENV HF_HOME=/models
ENV HF_HUB_DISABLE_TELEMETRY=1
COPY services/ai-assistant/scripts/download_hf_models.py /tmp/download_hf_models.py
RUN python /tmp/download_hf_models.py && rm /tmp/download_hf_models.py

COPY services/ai-assistant/app/ ./app/

ENV DATA_DIR=/app/data
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
