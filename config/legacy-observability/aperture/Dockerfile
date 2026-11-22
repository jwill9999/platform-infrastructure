FROM python:3.12-slim
RUN pip install --no-cache-dir boto3 cbor2 zstandard prometheus_client
COPY aperture_exporter.py /app/aperture_exporter.py
WORKDIR /app
CMD ["python3", "aperture_exporter.py"]
