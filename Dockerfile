FROM python:3.13-slim

LABEL org.opencontainers.image.authors="晨星"
LABEL org.opencontainers.image.title="aether-ai-core"
LABEL org.opencontainers.image.version="0.1.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt

COPY pyproject.toml README.md ./
COPY aether ./aether
COPY tools ./tools
COPY tests ./tests

RUN pip install --no-cache-dir -e .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://127.0.0.1:8000/health', timeout=3).status_code==200 else 1)"

CMD ["uvicorn", "aether.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
