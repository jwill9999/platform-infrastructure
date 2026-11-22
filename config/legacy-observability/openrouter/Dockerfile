FROM python:3.12-slim
RUN pip install --no-cache-dir prometheus_client
COPY openrouter_activity_exporter.py /app/openrouter_activity_exporter.py
WORKDIR /app
CMD ["python3", "openrouter_activity_exporter.py"]
