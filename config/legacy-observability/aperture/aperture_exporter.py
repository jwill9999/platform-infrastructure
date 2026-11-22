import io
import json
import os
import time
from datetime import datetime

import boto3
import cbor2
import zstandard
from prometheus_client import Counter, start_http_server

R2_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
BUCKET = os.environ["APERTURE_R2_BUCKET_NAME"]
ACCESS_KEY = os.environ["APERTURE_R2_ACCESS_KEY_ID"]
SECRET_KEY = os.environ["APERTURE_R2_SECRET_ACCESS_KEY"]
POLL_SECONDS = int(os.environ.get("APERTURE_EXPORTER_POLL_SECONDS", "60"))
STATE_FILE = "/state/processed_files.json"

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto",
)

cost_dollars_total = Counter(
    "aperture_estimated_cost_dollars_total",
    "Cumulative estimated cost in USD from Aperture usage exports",
    ["identity", "model", "cost_basis", "year_month"],
)
tokens_total = Counter(
    "aperture_tokens_total",
    "Cumulative token usage from Aperture usage exports",
    ["identity", "model", "token_type", "cost_basis", "year_month"],
)
requests_total = Counter(
    "aperture_requests_total",
    "Count of requests recorded in Aperture usage exports",
    ["identity", "model", "status_code", "cost_basis", "year_month"],
)


def record_year_month(record):
    """Calendar month the request actually happened, from the record's own
    timestamp — NOT when we processed/imported it. Needed because Prometheus's
    scrape-time semantics (increase()/rate()) can't correctly attribute
    batch-imported historical data to the period it actually occurred in."""
    ts = record.get("timestamp")
    if not ts:
        return "unknown"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m")
    except Exception:
        return "unknown"


def load_processed():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_processed(processed):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(processed), f)


def identity_label(record):
    identity = record.get("identity") or {}
    tags = identity.get("tags")
    if tags:
        return tags[0]
    return identity.get("login_name", "unknown")


def process_file(key):
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    compressed = obj["Body"].read()
    decompressed = zstandard.ZstdDecompressor().decompress(compressed, max_output_size=200_000_000)
    decoder = cbor2.CBORDecoder(io.BytesIO(decompressed))
    count = 0
    while True:
        try:
            record = decoder.decode()
        except Exception:
            break
        count += 1
        ident = identity_label(record)
        model = record.get("model", "unknown")
        status = str(record.get("status_code", "unknown"))
        year_month = record_year_month(record)

        est_cost = record.get("estimated_cost") or {}
        dollars = est_cost.get("dollars")
        cost_basis = est_cost.get("cost_basis", "unknown")

        requests_total.labels(identity=ident, model=model, status_code=status, cost_basis=cost_basis, year_month=year_month).inc()

        if dollars:
            cost_dollars_total.labels(identity=ident, model=model, cost_basis=cost_basis, year_month=year_month).inc(dollars)

        usage = record.get("usage") or {}
        for token_type, value in usage.items():
            if isinstance(value, (int, float)):
                tokens_total.labels(identity=ident, model=model, token_type=token_type, cost_basis=cost_basis, year_month=year_month).inc(value)

    print(f"[aperture-exporter] processed {key}: {count} records", flush=True)


def main():
    start_http_server(9200)
    print("[aperture-exporter] serving /metrics on :9200", flush=True)
    processed = load_processed()
    while True:
        try:
            resp = s3.list_objects_v2(Bucket=BUCKET)
            keys = [o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".cbor.zstd")]
            new_keys = sorted(k for k in keys if k not in processed)
            for key in new_keys:
                process_file(key)
                processed.add(key)
                save_processed(processed)
        except Exception as e:
            print(f"[aperture-exporter] error: {e}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
