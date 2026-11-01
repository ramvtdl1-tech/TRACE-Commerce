FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 DATABASE_PATH=/app/data/commerce.sqlite3
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home commerce
COPY --chown=commerce:commerce commerce ./commerce
COPY --chown=commerce:commerce static ./static
COPY --chown=commerce:commerce catalog.json ./catalog.json
RUN mkdir -p /app/data && chown commerce:commerce /app/data
USER commerce
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/healthz',timeout=3)"
CMD ["sh", "-c", "exec uvicorn commerce.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-access-log"]
