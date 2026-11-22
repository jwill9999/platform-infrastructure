# Legacy observability recovery snapshot

Secret-free reference configuration captured from the running self-hosted stack on
22 November 2026. See
[the inventory](../../docs/observability-inventory.md) for provenance, limitations,
dependencies, and retention policy.

This directory is not a deployable backup. It includes a path-adjusted Compose
reference and custom build sources, but intentionally excludes credentials,
addresses, database state, telemetry, logs, provider payloads, and owner credential
files. `TAILSCALE_IP` is a non-secret placeholder; no `.env` file is retained.
Every retained file passed the native Sonar secrets scanner before publication.

The retained dashboard preserves the original provider-compatible `files/`
subdirectory. Do not infer deployability from internal path consistency; live
runtime environment, credential, and state material remains excluded.
