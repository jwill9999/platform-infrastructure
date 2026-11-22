# Agent instructions

These rules apply to work in this repository.

## Scope and tracking

- GitHub Issues is the sole live task tracker. Do not create a parallel Markdown
  backlog or infer that a merged change is operationally accepted.
- Keep shared infrastructure here rather than duplicating it in application
  repositories. Application issues may link to an infrastructure dependency.
- Use small, dependency-ordered issues with explicit acceptance, rollback, and
  cleanup criteria.

## Secrets and private data

- Never commit credentials, access tokens, cookies, private keys, provider usage
  payloads, raw logs, prompts, responses, VM disks, signed artefacts, or Grafana
  exports that embed secure fields.
- Store runtime credentials in the narrowest supported secret store. Separate
  administration, telemetry-write, provider-read, notification, runner, and
  signing credentials.
- Before reading a workspace file, run `sonar analyze secrets <path>`. If it
  reports a secret, do not read the file; stop and ask the owner to rotate and
  remove the value.
- Treat command output, screenshots, diagnostics, and generated plans as possible
  secret-bearing material. Redact values rather than copying them into evidence.
- Follow [the credential runbook](docs/security-and-credentials.md) for storage,
  owner handoff, rotation, revocation, and suspected exposure. Agents may define
  secret names and destinations but must never request or receive secret values in
  chat.

## Change workflow

- Begin with read-only inventory and current vendor documentation.
- Prefer maintained services and integrations before bespoke daemons, webhooks,
  schedulers, collectors, or control planes.
- Present any new custom component boundary, security model, ongoing cost, and
  qualification plan for owner agreement before implementation.
- Use feature branches and pull requests. Do not push directly to `main`.
- Obtain meaningful read-only critique of substantial architecture, security,
  lifecycle, and migration changes before implementation or acceptance.
- Keep third-party GitHub Actions pinned to full commit SHAs. Review their source,
  permissions, and release provenance before updating a pin.

## Practical verification

- Static validation and green CI do not establish infrastructure acceptance.
- Define finite resource, cost, API-call, and time limits before live changes or
  disruptive tests.
- Verify alert delivery from outside the monitored system. A dashboard on the VPS
  cannot prove detection of total VPS loss.
- Use guaranteed teardown and exact ownership checks for containers, processes,
  temporary files, test endpoints, runner workspaces, and credentials.
- Do not stop or delete resources whose ownership is unclear. Reconcile them first.
- Retain only compact evidence and reviewed rollback material. Remove disposable
  state after shutdown, ownership, and recovery checks.

## Documentation

- Plans describe approved architecture and stable boundaries; issues own live
  status, claims, blockers, and concise evidence.
- Distinguish proposed, configured, tested, accepted, published, and retired.
- Preserve important failed tests without presenting them as current blockers after
  resolution.
- Every operational alert requires an owner, notification route, first response,
  escalation condition, and recovery check.
