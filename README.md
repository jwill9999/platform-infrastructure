# Platform infrastructure

Private configuration, planning, and operational runbooks for shared development
infrastructure owned by `jwill9999`.

Initial scope:

- Grafana Cloud migration and external VPS monitoring.
- Codex, Claude, and OpenRouter usage dashboards.
- Shared VPS resource and container lifecycle safeguards.
- A later self-hosted macOS GitHub Actions runner and its Tailscale-supported
  operational boundary.

GitHub Issues owns live task status and acceptance evidence. Repository documents
own reviewed architecture, configuration, and runbooks. Secrets, raw telemetry,
private logs, VM disks, build artefacts, and credential-bearing exports must not be
committed.

See [the observability migration plan](docs/planning/observability-migration.md).
