FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps chromium
COPY . .
RUN mkdir -p /data /app/reports /app/screenshots
EXPOSE 5000
CMD ["python", "-m", "erp.app"]
