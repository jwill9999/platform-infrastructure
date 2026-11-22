# Observability migration plan

Status: reviewed migration plan. No Grafana Cloud, Hostinger, provider, or VPS
configuration change is authorised by this document.

## Objective

Move the current self-hosted Grafana, Prometheus, Loki, and AI-usage monitoring
toward an externally hosted Grafana Cloud control plane so monitoring and alerts
remain available when the VPS is unavailable. Add bounded host metrics and external
availability checks, preserve the existing Codex, Claude, and OpenRouter usage
views, then retire local components only after parallel qualification and rollback
review.

Fourteen days of infrastructure telemetry retention is currently sufficient.
Longer-term agent observability, prompt/trace storage, and product telemetry are
not part of this migration.

## Current discovery snapshot

Read-only inspection on 22 November 2026 found:

- Ubuntu VPS, approximately 7.7 GiB RAM, 4 GiB swap, and a 96 GiB root filesystem.
- Docker services `obs-grafana`, `obs-prometheus`, `obs-loki`, and
  `obs-openrouter-activity-exporter`, bound to the Tailscale address where exposed.
- Prometheus uses a 90-day local retention setting. Grafana, Prometheus, and Loki
  use persistent Docker volumes and owner-local configuration under
  `/home/letuscode/observability`; file contents and credentials were not read.
- The observability containers were running during inspection but were not
  functionally tested. Their observed memory was not the main source of exhaustion.
- Thirty-nine unintended Docker SonarQube MCP containers had consumed nearly all
  RAM and swap. With owner approval they were stopped and auto-removed. Available
  memory recovered from roughly 156 MiB to 5.7 GiB and swap use fell from roughly
  4 GiB to 840 MiB.
- Subsequent read-only qualification tied new containers to the Codex SonarQube MCP
  integration: SonarQube CLI 1.11.0 returned while its auto-remove stdio container
  remained alive with no CPU, memory, or PID limit. The owner chose to disable the
  container-based MCP integration rather than introduce a custom lifecycle wrapper.
  The Codex MCP configuration entry, one remaining Docker container, and the
  separate Podman MCP container were removed. The native CLI and secret-scanning
  hook were retained. Two native scans plus an independent fresh-agent recheck
  passed without recreating an MCP container; the observability stack remained
  running. Available memory was about 5.5 GiB and swap use about 607 MiB at final
  author verification.

The Sonar event is planning evidence for container ownership, missing-telemetry,
resource saturation, and cleanup alerts. It is not proof that the future monitoring
design detects those conditions.

## Proposed target architecture

1. Grafana Cloud is the authoritative dashboard, hosted metrics, alert evaluation,
   and notification plane.
2. Grafana Alloy on the VPS collects bounded Linux and selected service metrics and
   sends them directly to Grafana Cloud using a write-only credential.
3. No local Prometheus is retained unless inventory finds a concrete unsupported
   scrape, recording-rule, or local-consumer requirement.
4. A genuinely off-VPS probe checks an agreed safe endpoint. The preferred option
   is a minimal public HTTPS health endpoint plus Grafana Cloud Synthetic
   Monitoring; if public exposure is rejected, another always-on host must run a
   maintained private probe. A probe on this VPS cannot establish total VPS loss,
   and the MacBook is not assumed continuously available. A missing-telemetry rule
   independently detects Alloy or host disappearance.
5. Codex, Claude, and OpenRouter usage remains dynamically queried from maintained
   provider APIs through Grafana Cloud Infinity where compatible. Provider history
   is not copied into telemetry unless a later requirement justifies it.
6. Hostinger hPanel remains an independent provider-level diagnostic and recovery
   view.
7. Tailscale may protect operational endpoints and assist private diagnostics, but
   it does not replace application authentication, alert evaluation, admission, or
   external failure detection.

## Security boundary

- Use separate credentials for Grafana administration, Alloy remote write,
  provider read-only usage access, alert delivery, and any later runner.
- Never place provider or Grafana credentials in Git, issue text, dashboards,
  labels, logs, screenshots, or exported evidence.
- Prefer read-only organisation-scoped provider credentials. Record when a vendor
  cannot provide least-privilege usage access and obtain owner acceptance of that
  residual risk.
- Do not expose Prometheus, Alloy, administrative Grafana, Docker, or general debug
  endpoints publicly.
- A health endpoint must disclose no private state and must not provide a control
  action.
- Restrict Infinity allowed hosts and HTTP methods. Destructive methods stay off.
- Store the Alloy write credential in a root-owned `0600` environment file or a
  maintained container-secret mechanism; never in its committed configuration.
- Store provider data-source credentials only in Grafana Cloud secure fields, using
  restricted read-only keys where available. Store notification credentials in the
  maintained Grafana Cloud contact-point secret mechanism.
- Start with reviewed secret-free Alloy files and Grafana dashboard/alert JSON.
  Terraform is deferred unless scale justifies it; Terraform state must use an
  encrypted remote backend because state may contain secrets.

## Migration phases

### 1. Immediate helper-container containment — completed 22 November 2026

- The owner selected removal of the container-based SonarQube MCP integration while
  retaining the native CLI scanner and repository secret-scanning protocol.
- Future re-enablement requires a maintained fix or a separately reviewed lifecycle
  boundary with stable ownership, finite resource/lifetime limits, guaranteed
  teardown, and stale reconciliation.
- Resource monitoring should still alert on abnormal container count and memory,
  but detection is not a substitute for lifecycle prevention.

### 2. Repository and access baseline — completed 22 November 2026

- Repository governance, owner roles, secret destinations, branching, review,
  incident response, and evidence boundaries are defined in
  [the security and credential runbook](../security-and-credentials.md).
- `main` is protected by an active no-bypass ruleset requiring pull requests,
  blocking deletion and non-fast-forward updates, and requiring the exact
  GitHub Actions contexts `Secret scan` and `Repository structure` with strict
  branch updating.
- PR #14 published the baseline after native scans, structural validation, and an
  independent security critique. Both hosted checks passed on revision
  `1b373b1e1beb08ab3c3278b08039c9717cfd83a9`.
- Temporary PR #15 added one harmless generated file one byte above the 1 MiB
  policy ceiling. `Secret scan` passed, `Repository structure` failed, and GitHub
  reported the PR as `BLOCKED`. The PR was closed, its remote branch deleted, and
  its temporary checkout removed without merging the probe.
- PR #14 merged as `27c1f19e8e8ac9be7b4cdf00f99f0ff9edd07e66`.
  Post-merge native scans and structural validation passed, the ruleset readback
  retained both required contexts with no bypass actors, and the exact merge
  revision's push workflow passed.
- Read-only Grafana Cloud organisation and stack discovery remains part of phase 4;
  no Grafana Cloud access or configuration was qualified by this repository phase.

### 3. Inventory and export

- Inventory versions, Docker Compose ownership, volumes, restart policies, network
  boundaries, dashboards, data sources, alerts, notification policies, Prometheus
  targets/rules, Loki use, and the OpenRouter exporter.
- Export sanitised dashboard and alert definitions. Verify exports contain no
  secure fields before adding reviewed configuration to Git.
- Measure current resource usage, active series, scrape intervals, API refresh
  rates, data ranges, and local disk retention.
- Identify every consumer of local Prometheus/Loki and every feature that cannot be
  reproduced directly in Grafana Cloud.
- Record the owner decision that the current 90-day local Prometheus history may be
  discarded after parallel qualification; no historical migration is currently
  required. Retain rollback configuration only through cutover plus an agreed
  review window, then review it for deletion.
- Sanitise through supported Grafana/Prometheus export mechanisms or owner-operated
  redaction. Agents must not bypass the secret-scanning rule to read a
  credential-bearing source file.

### 4. Grafana Cloud foundation

- Create infrastructure and AI-usage folders in the selected stack.
- Configure least-privilege service identities, external notification contact
  points, notification policies, and a test alert independent of the VPS.
- Enable Grafana Cloud usage/limit monitoring.
- Export a secret-free recovery representation of created dashboards and rules.
- Configure maintenance silences with mandatory expiry, explicit no-data/error
  behavior, grouping/deduplication, recovery notifications, and a scheduled
  end-to-end alert-path test.

### 5. AI-usage dashboards

- Migrate Codex/OpenAI, Claude/Anthropic, and OpenRouter views one at a time.
- Verify authentication, pagination, provider reporting delay, time zones, rate
  limits, refresh intervals, empty results, stale results, and API failures.
- Never display an authentication/query failure as zero spend or zero activity.
- Decide whether the current OpenRouter exporter remains necessary. Retire it only
  after direct queries or a replacement pipeline produce equivalent reviewed data.
- Treat Codex, OpenAI organisation usage, Claude, and OpenRouter as separate source
  contracts. For each, record the maintained endpoint, credential scope,
  pagination, reporting delay, rate limit, available time range, and Infinity
  compatibility before choosing direct access.

### 6. VPS telemetry

- Deploy a pinned, resource-bounded Alloy configuration through a reviewed change.
- Collect CPU/load/steal, available memory, swap activity, filesystem capacity,
  inodes, disk I/O and latency, network, uptime, and Alloy health through the
  maintained Linux integration.
- Evaluate maintained candidates separately for container metrics and event data:
  cAdvisor or a supported Docker metrics endpoint for cgroups/containers, and
  narrowly filtered journald/log collection for OOM/service-exit events. Docker
  socket, host PID/cgroup, journal, or broad filesystem access requires explicit
  owner approval. A read-only Docker socket remains control-equivalent exposure and
  is not mounted silently.
- Filter labels and collectors to prevent cardinality growth and private-data
  capture. Bound retry/WAL storage and define behavior during cloud unavailability.
- Initial deployment ceilings to validate: 30-second host scrape interval; no more
  than 2,000 active series for this VPS; 256 MiB Alloy memory; 0.25 average CPU core
  outside startup; 512 MiB telemetry WAL/retry storage; and at least 10 GiB root
  filesystem reserve. Reaching a local ceiling must shed or stop telemetry safely
  and alert externally rather than consume recovery capacity.

### 7. Independent availability

- Select the independent probe vantage point and health endpoint policy.
- Add the external availability check and a separately evaluated missing-telemetry
  rule. Verify the available signals distinguish application, endpoint, Tailscale,
  collector, probe, and whole-host failures without overstating certainty.
- Define endpoint authentication/disclosure, probe credentials, rate limits, and
  behavior during planned maintenance.

### 8. Parallel qualification

- Run cloud and self-hosted monitoring concurrently for an agreed observation
  window.
- Compare infrastructure and provider values, alert firing/recovery, query costs,
  series usage, and data freshness.
- Exercise bounded CPU, memory, disk, collector interruption, cloud-connectivity,
  service-health, and whole-VPS-loss scenarios with owner-approved limits.
- Confirm alert delivery through a channel independent of the VPS.
- Verify reboot recovery, bounded local buffering, and no secret leakage.

### 9. Authoritative cutover

- Declare Grafana Cloud authoritative only after acceptance evidence and critique.
- Freeze the local dashboards, retain reviewed rollback exports, disable local alert
  evaluation, and observe the cloud system for an agreed window.

### 10. Local-stack retirement

- Stop and remove only the owned local Grafana, Prometheus, Loki, exporter,
  containers, volumes, credentials, and configuration selected for retirement.
- Verify recovered resources, absent listeners/processes, preserved unrelated
  services, cloud monitoring health, and rollback disposition.

## Initial alert policy candidates

Thresholds remain proposals until baseline observation:

- CPU warning above 80% for 10 minutes; critical above 95% for 5 minutes.
- Available memory warning below 15%; critical below 8%.
- Sustained swap-in/swap-out and swap exhaustion.
- Filesystem/inode warning at 80–85%; critical at 90–95%.
- Sustained I/O wait or load materially above vCPU capacity.
- Immediate OOM event and unexpected critical-service exit.
- Abnormal container count or aggregate container memory, including a guard against
  repeated per-session helper accumulation.
- Missing telemetry for multiple collection intervals.
- Confirmed external availability failure.
- Provider usage query authentication, rate-limit, pagination, or stale-success
  failure.
- Grafana Cloud free-plan usage approaching a hard limit.

Every alert must define owner, severity, notification route, evaluation period,
first response, escalation, recovery condition, and noise-review trigger.

## Edge cases and failure semantics

- Missing data must not appear as a healthy zero.
- Hostinger memory graphs may include reclaimable cache; host alerts should use
  available memory and pressure signals.
- Compilation and dependency installation can cause legitimate short peaks.
- CPU credits/throttling and CPU steal may impair performance without matching a
  simple utilisation threshold.
- Alloy retry data must not fill the disk during network or Grafana Cloud outages.
- Clock skew can make healthy telemetry appear stale.
- Provider usage data may be delayed, paginated, eventually corrected, or absent
  during vendor incidents.
- Direct API dashboards can create rate limits or costs through aggressive refresh.
- Organisation usage APIs may require broader credentials than desired.
- Grafana Cloud or notification-provider failure needs an independent fallback;
  Hostinger hPanel remains available but is not the primary alert channel.
- Planned maintenance requires expiring silences; an indefinite silence is a
  monitoring failure. No-data and evaluation errors must have explicit alert states.
- Duplicate alerts need grouping and deduplication; every firing alert needs a
  recovery notification and a periodic end-to-end delivery test.
- A Tailscale-only check cannot distinguish a tailnet failure from a host failure
  without another signal.
- Public health checks must not expand the attack surface.
- Removing local volumes before rollback verification can destroy the only copy of
  dashboard history or configuration.

## Proposed issue tree

1. Contain and reconcile orphaned helper-container accumulation.
2. Establish repository governance and secret-handling baseline.
3. Inventory and sanitise the existing observability stack.
4. Configure the Grafana Cloud foundation and external notification test.
5. Migrate Codex, Claude, and OpenRouter usage dashboards.
6. Deploy bounded VPS host telemetry.
7. Establish independent VPS/application availability monitoring.
8. Qualify cloud monitoring in parallel with the local stack.
9. Cut over authoritative monitoring to Grafana Cloud.
10. Retire the owned self-hosted observability stack.
11. Plan and qualify the self-hosted Mac GitHub Actions runner separately.

Issue 1 is immediate containment and does not wait for repository process work.
Issues 2–3 precede cloud changes. Issue 4 precedes issues 5–8. Issues 5, 6, and 7
may proceed independently after issue 4, but all precede issue 8. Issues 8, 9, and
10 are sequential gates. Issue 11 shares the repository security baseline but is
not part of observability acceptance.

## Acceptance boundary

Migration acceptance requires trustworthy dashboards, externally evaluated and
delivered alerts, whole-VPS-loss detection, honest missing/stale data, bounded
collector storage/cardinality, secure credential handling, reviewed rollback,
verified local-stack cleanup, and an independent critique with resolved findings.

Creating the repository or closing individual implementation issues does not by
itself establish migration acceptance.
