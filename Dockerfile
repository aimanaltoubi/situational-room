FROM python:3.11-slim

# H2O (used for ML predictions) needs a JRE
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
EXPOSE 5000

# Run the pipeline once at image build time is NOT done here since it needs
# secrets/API keys — run it at container start instead, then serve.
CMD for w in $(ls workspaces); do python3 run_pipeline.py -w "$w" --skip-scrape || true; done; gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
