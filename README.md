# Platform infrastructure

Configuration, planning, and operational runbooks for shared development
infrastructure owned by `jwill9999`. The repository is currently public, so every
tracked file must be safe for unrestricted disclosure.

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

See:

- [Observability migration plan](docs/planning/observability-migration.md)
- [Existing observability inventory](docs/observability-inventory.md)
- [Security and credential handling](docs/security-and-credentials.md)
