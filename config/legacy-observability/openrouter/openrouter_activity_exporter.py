import json
import os
import threading
import time
import urllib.request

from prometheus_client import Gauge, start_http_server

POLL_SECONDS = 5 * 60  # activity data is daily-granularity; polling every 5 min is plenty (matches the Aperture exporter's cadence)
ACTIVITY_URL = "https://openrouter.ai/api/v1/activity"
CREDITS_URL = "https://openrouter.ai/api/v1/credits"
MANAGEMENT_KEY = os.environ["OPENROUTER_MANAGEMENT_KEY"]

cost_dollars = Gauge(
    "openrouter_activity_cost_dollars",
    "Cost in USD by date and model, last 30 UTC days",
    ["date", "model"],
)
requests_total = Gauge(
    "openrouter_activity_requests",
    "Request count by date and model, last 30 UTC days",
    ["date", "model"],
)
tokens_total = Gauge(
    "openrouter_activity_tokens",
    "Token count by date, model and token_type (prompt/completion/reasoning/cached), last 30 UTC days",
    ["date", "model", "token_type"],
)
credits_total_dollars = Gauge(
    "openrouter_credits_total_dollars",
    "Total credits ever purchased, all-time (not scoped to the 30-day activity window)",
)
credits_used_dollars = Gauge(
    "openrouter_credits_used_dollars",
    "Total credits used, all-time (not scoped to the 30-day activity window)",
)
collection_success = Gauge(
    "openrouter_activity_collection_success",
    "1 if the last poll succeeded, else 0",
)
last_success_timestamp = Gauge(
    "openrouter_activity_last_success_timestamp_seconds",
    "Unix timestamp of the last successful poll",
)


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {MANAGEMENT_KEY}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_activity():
    return fetch_json(ACTIVITY_URL)


def fetch_credits():
    return fetch_json(CREDITS_URL)


def poll_once():
    result = fetch_activity()
    rows = result.get("data") or []

    cost = {}
    req_counts = {}
    tokens = {}
    for row in rows:
        date = row.get("date")
        model = row.get("model")
        if not date or not model:
            continue
        date = date.split(" ")[0].split("T")[0]  # OpenRouter's date field includes a time component; keep just YYYY-MM-DD
        key = (date, model)
        cost[key] = cost.get(key, 0.0) + (row.get("usage") or 0.0)
        req_counts[key] = req_counts.get(key, 0) + (row.get("requests") or 0)
        for token_field in ("prompt_tokens", "completion_tokens", "reasoning_tokens", "cached_tokens"):
            label = token_field.replace("_tokens", "")
            tkey = (date, model, label)
            tokens[tkey] = tokens.get(tkey, 0) + (row.get(token_field) or 0)

    cost_dollars.clear()
    requests_total.clear()
    tokens_total.clear()
    for (date, model), usd in cost.items():
        cost_dollars.labels(date=date, model=model).set(usd)
    for (date, model), count in req_counts.items():
        requests_total.labels(date=date, model=model).set(count)
    for (date, model, token_type), count in tokens.items():
        tokens_total.labels(date=date, model=model, token_type=token_type).set(count)

    credits = fetch_credits().get("data") or {}
    if credits.get("total_credits") is not None:
        credits_total_dollars.set(credits["total_credits"])
    if credits.get("total_usage") is not None:
        credits_used_dollars.set(credits["total_usage"])

    collection_success.set(1)
    last_success_timestamp.set(time.time())
    print(f"[openrouter-activity-exporter] poll ok, {len(rows)} rows, {len(cost)} date/model pairs", flush=True)


def poll_loop():
    while True:
        try:
            poll_once()
        except Exception as e:
            collection_success.set(0)
            print(f"[openrouter-activity-exporter] error: {e}", flush=True)
        time.sleep(POLL_SECONDS)


def main():
    start_http_server(9202, addr="0.0.0.0")
    print("[openrouter-activity-exporter] serving /metrics on :9202", flush=True)
    poll_loop()


if __name__ == "__main__":
    main()
