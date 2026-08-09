# Dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY tests/ tests/
COPY fixtures/ fixtures/
COPY Makefile .
RUN useradd -m appuser
USER appuser
ENTRYPOINT ["python", "-m", "coding_harness"]
CMD ["--help"]
