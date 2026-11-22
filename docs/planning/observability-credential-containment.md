# Observability credential containment plan

Status: proposed for owner approval and independent security critique. This plan
does not authorise credential creation, rotation, revocation, container recreation,
notification delivery, or deletion.

Owning issue: GitHub Issue #17. Prerequisite inventory: GitHub Issue #4 and
[`docs/observability-inventory.md`](../observability-inventory.md).

## Objective

Replace the shared Compose `.env` boundary with per-service secrets, rotate every
populated credential exposed to an unrelated container, remove stale credential
copies from owned containers and disk, and preserve the running monitoring stack
with a bounded rollback path.

## Confirmed current risk

Boolean-only Docker inspection confirmed populated Grafana administration, Slack,
OpenRouter, Loki object-storage, and legacy Aperture object-storage credential
classes in containers that do not require them. No value was emitted or copied.
Docker administrators will inherently retain access to container environments;
this task reduces cross-service exposure but does not create a defence boundary
against VPS root or Docker-root compromise.

## Target mapping

Store per-service files outside Git under the owner-controlled Compose directory in
a `secrets/` directory with directory mode `0700` and file mode `0600`. The Compose
owner creates and populates them directly; agents may verify names, permissions,
ownership, and boolean population but never values.

| Service | Required secret classes | Target file | Notes |
| --- | --- | --- | --- |
| Grafana | Slack webhook only | `secrets/grafana.env` | Existing administrator password remains only in the owner's password manager |
| Loki | R2 account identifier, bucket, access key, secret key | `secrets/loki.env` | Scope replacement credentials to the Loki bucket and required object operations |
| OpenRouter exporter | OpenRouter management/usage key only | `secrets/openrouter.env` | Preserve account-wide activity and credit-read behavior only |
| Prometheus | None | None | Do not add an environment file |
| Aperture exporter | None while retired | None | Keep disabled; do not preserve a live credential merely for speculative rollback |

Remove the existing Grafana `GF_SECURITY_ADMIN_PASSWORD` Compose mapping entirely;
service `env_file` values do not participate in Compose interpolation and the
bootstrap variable does not rotate an existing database user. Disaster recovery
requires a separate owner-operated, one-time bootstrap procedure that injects a
new value without retaining it in Compose or a container environment.

The Compose source must reference only the corresponding service file. The legacy
Aperture service should move behind an explicit disabled profile with no default
credential source. Its stopped container must be removed after its credential is
revoked, while its image, source snapshot, state volume, and R2 data remain intact
for the later retirement decision.

## Owner-operated rotation sequence

### 1. Preflight and rollback capture

- Confirm the exact Compose revision, running container IDs, image digests, volume
  names, service health, dashboard availability, five alert definitions, two
  Prometheus targets, and current exporter last-success timestamps.
- Confirm at least 10 GiB free disk and 2 GiB available memory.
- Validate the secret-free recovery snapshot and prepare a reversible Compose
  patch. The owner applies that patch to the owner-controlled source because the
  agent cannot write it. Do not copy the old `.env` into Git or agent-visible
  output.
- Validate Compose structure before secret files are populated. Never print,
  capture, or retain expanded `docker compose config` output after population;
  post-population validation may use only exit status and redacted/name-only
  checks.
- Retain the prior Compose revision, exact image digest, volume identity, and
  still-valid old credential until each replacement passes. A fixed-name Compose
  recreation replaces the old container; do not claim the old container itself is
  available for rollback.

### 2. Prepare isolated secret files

- The owner creates each replacement credential at its provider and places it
  directly into the matching `0600` file.
- Do not place credentials in shell history, command arguments, chat, screenshots,
  issues, logs, or temporary world-readable files.
- Validate only file ownership/mode, expected variable names, and non-empty values.

### 3. Rotate and recreate Loki

- Create a bucket-scoped R2 credential with only the list/read/write/delete
  operations Loki requires; record any provider limitation.
- Update only `secrets/loki.env`, patch the Loki `env_file`, and recreate only Loki.
- Verify readiness, a harmless empty/recent query, absence of new storage/auth
  errors, unchanged local volume ownership, and unchanged Grafana data-source
  health.
- If the owner approves, validate the new R2 credential outside Loki with one
  uniquely named, non-sensitive canary object: create, list/read, delete, and
  absence readback. This proves the required object permissions without inserting
  production-like log content. If not approved, write/delete qualification remains
  an explicit open gate and Loki rotation is not accepted.
- After verification, revoke the previous Loki storage credential and confirm the
  provider reports it inactive.

### 4. Rotate and recreate the OpenRouter exporter

- Create the narrowest supported account-usage/credits credential. If OpenRouter
  cannot restrict the management key to those reads, record and approve the
  residual scope before creation.
- Update only `secrets/openrouter.env`, patch its `env_file`, and recreate only the
  exporter.
- Allow at most two polls and ten minutes. Verify collection success, a newer
  last-success timestamp, expected metric families, bounded series count, and no
  secret-bearing error output.
- Revoke the prior key and confirm it is inactive at the provider.

### 5. Rotate Grafana administration and Slack

- The owner creates a replacement Slack webhook for the intended destination and
  enters it directly into `secrets/grafana.env`.
- The owner rotates the existing Grafana administrator password through the UI or
  `grafana cli admin reset-admin-password --password-from-stdin`; never pass it as
  a command argument. Store it only in the owner password manager.
- Remove the Compose administrator-password mapping, patch Grafana to use
  `secrets/grafana.env` only for Slack, and recreate only Grafana.
- Verify database health, the provisioned dashboard, two data sources, five alert
  rules, and notification routing. Create one temporary uniquely named test alert
  routed only to the replacement contact point; verify one firing and one recovery
  outside the VPS, then delete the alert and verify its absence. Do not alter or
  force a real quota/credit rule.
- Revoke the old Slack webhook and verify the old Grafana password is rejected.

### 6. Revoke legacy Aperture access and remove stale copies

- Revoke the Aperture R2 credential without deleting its bucket or objects.
- Remove the stopped `obs-aperture-exporter` container only after confirming its
  source, image identity, and named state volume are retained. Keep the service
  disabled behind an explicit profile.
- After all replacements and revocations pass, prove no active/stopped owned
  container contains unrelated credential-class variable names.
- Prove the old shared `.env` is no longer referenced, then remove that exact file.
  Preserve no revoked values for rollback; rollback uses newly created scoped
  credentials.

## Finite execution limits

- One owned container recreated at a time with
  `docker compose up -d --no-deps --force-recreate <service>` (or an equivalent
  reviewed exact-service command); never run `docker compose down`. Read back
  container IDs to prove no dependent service was recreated.
- No volume, image, R2 bucket, existing R2 object, dashboard, existing alert, or
  Prometheus data deletion. The uniquely owned R2 canary object and temporary test
  alert must be deleted as part of their guaranteed cleanup.
- A replacement must become healthy within five minutes or rollback begins. Once
  health is restored, remaining verification may continue for at most ten minutes
  total per service, with at most two ordinary verification attempts per provider
  operation. The approved R2 canary cycle is separately limited to one
  create/list-read/delete/absence sequence.
- Stop if two services are unhealthy simultaneously, available memory falls below
  2 GiB, root free space falls below 10 GiB, or an unrelated container changes.
- One Slack firing and one recovery notification only, with owner approval.
- No paid provider operation beyond ordinary credential creation, bounded
  verification, and the approved canary cycle; stop if a provider presents an
  unexpected charge or broad scope.

## Rollback

Before old-credential revocation, rollback means restore the prior Compose service
definition and recreate only the failed service with the still-valid prior secret.
After revocation, never restore a revoked value: create another narrowly scoped
credential and use the retained image/config/volume. If verification cannot finish
inside the limit, restore service availability, retain the split-file boundary
where safe, record the unresolved gate, and stop.

## Acceptance evidence

- Per-container environment-name and non-empty checks show only required classes.
- Provider-side state confirms every superseded credential is revoked/inactive.
- The owner performs a negative old-credential check where the provider supports a
  safe bounded attempt. When it does not, retain provider-confirmed revocation and
  an explicit accepted limitation rather than exposing the old value.
- Grafana, Loki, Prometheus, OpenRouter exporter, alerts, and notification recovery
  pass their bounded checks; Prometheus and unrelated workloads remain unchanged.
- The legacy Aperture container and shared `.env` are absent, while the Aperture
  image/source/state volume and R2 data remain explicitly retained.
- No value appears in Git, GitHub, agent-visible output, logs, or retained evidence.
- Independent security and cleanup critique approves the final state.

## Owner decisions required before execution

1. Approve the per-service file boundary and residual Docker-root visibility.
2. Approve revoking legacy Aperture access and removing only its stopped container,
   while retaining its volume, image, source, and R2 data.
3. Approve the stated per-service interruption, API-call, and resource limits.
4. Approve one Slack test firing and recovery notification.
5. Approve one non-sensitive R2 canary create/list-read/delete/absence cycle.
6. Confirm owner access to Cloudflare R2, OpenRouter, Slack, Grafana, and the
   Compose directory for direct secret creation and entry.
