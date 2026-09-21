FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY planprobe ./planprobe
COPY synthetic_app ./synthetic_app
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["sh", "-c", "uvicorn planprobe.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
