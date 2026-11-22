# Existing observability inventory

Status: read-only inventory captured 22 November 2026 for migration planning. No
service, credential, dashboard, alert, volume, or provider configuration was
changed. Runtime values and addresses are deliberately omitted because this
repository is public.

## Inventory boundary

The inventory used Docker metadata, bounded health/API queries, Prometheus TSDB
metadata, Grafana metadata counts, process/service metadata, and individually
secret-scanned configuration copies. The agent did not access the owner-controlled
Compose path directly; it reviewed temporary scoped copies supplied by the owner
after each passed secret scanning. It did not read credential values, provider
payloads, raw metrics, log streams, prompts, or responses. Temporary source,
database, and log copies were used only for bounded checks and were not retained.

The Compose directory was inaccessible to this agent account. The owner supplied
temporary, narrowly scoped copies of the Compose file and custom build sources;
each passed secret scanning before review. The recovery snapshot in
[`config/legacy-observability`](../config/legacy-observability) preserves their
effective structure with a tailnet placeholder. It remains a sanitised reference,
not a deployable backup, because secrets and live state are intentionally absent.
Both retained custom exporter sources matched the corresponding running or stopped
container files by SHA-256; the hashes were used only for comparison and the
temporary runtime copy was deleted.

## Runtime topology

One Docker Compose project named `observability` owns a bridge network and these
containers:

| Component | Observed version | State | Persistence | Limit | Function |
| --- | --- | --- | --- | --- | --- |
| Grafana | 13.3.1 | Running | Named volume plus read-only provisioning binds | 512 MiB RAM / 1 GiB RAM+swap | Dashboard, data-source, and alert UI/evaluation |
| Prometheus | 3.16.0 | Running | Named TSDB volume plus read-only config bind | 512 MiB / 1 GiB | Scrapes two targets and receives OTLP metrics |
| Loki | 3.7.10 | Running | Small named local volume plus R2 object storage | 512 MiB / 1 GiB | Configured log store; no active ingestion established |
| OpenRouter activity exporter | Custom Python image | Running | None | 128 MiB / 256 MiB | Polls account-wide activity and credits every five minutes |
| Aperture exporter | Custom Python image | Exited with code 137 | 172-byte named state volume | 256 MiB / 512 MiB | Superseded; retained but not scraped |

All five use `unless-stopped`. None has an explicit CPU or PID limit. The three
upstream images use mutable `latest` tags; the running image digests were
identified locally but are not yet pinned in source configuration. Grafana,
Prometheus, and Loki are published only on a tailnet address. The exporter has no
published port and is reached on the Compose network.

At the read-only sample, the four running containers used about 570 MiB RAM and
roughly 3% aggregate Docker CPU. Named data volumes used approximately 184 MiB for
Grafana, 31 MiB for Prometheus, 49 KiB locally for Loki, and 172 bytes for the
stopped Aperture exporter. The root filesystem had about 67 GiB available. These
are point-in-time observations, not capacity guarantees.

## Metrics producers and consumers

Prometheus is configured for a one-minute scrape interval, a 90-day retention
period, and the OTLP HTTP receiver. Its two scrape targets were healthy:

- Prometheus self-monitoring;
- the OpenRouter activity exporter on the private Compose network.

The TSDB head reported 23,104 series during inspection. Retained blocks covered
about 166 hours and occupied about 31 MiB, so the configured 90-day ceiling is not
the same as 90 days of existing data.

Additional producers push through OTLP rather than appearing in `scrape_configs`:

- active Codex processes emit high-cardinality native operational telemetry;
- an enabled user systemd service polls Codex subscription/rate-limit state every
  minute through `codex app-server`;
- an enabled user systemd service polls Claude subscription usage every minute and
  reads and refreshes the owner's Claude credential file in place;
- Claude Code emits session, token, active-time, and notional-cost metrics.

The Codex native telemetry accounts for most active series and includes extensive
histogram families. It cannot fit unfiltered within the plan's proposed 2,000-series
total-VPS budget if that budget is intended to include agent telemetry. The usage
dashboard needs only a small subset of subscription and usage series. A separate
agent-observability cardinality budget remains undecided, so native operational
telemetry must not be included implicitly in the host-integration migration.

Grafana is the only established Prometheus consumer. No recording or Prometheus
alert rules were configured. The accepted owner decision remains that local TSDB
history does not need migration after parallel qualification.

## Grafana objects

Grafana contains:

- one provisioned dashboard, `VPS Agents - Usage & Cost`, with 28 panels and a
  five-minute refresh;
- two provisioned data sources: Prometheus (default) and Loki;
- five provisioned Grafana-managed alert rules;
- one Slack contact point whose webhook is supplied through an environment
  placeholder.

The dashboard combines Claude Code usage/notional cost, Claude subscription quota,
Codex subscription quota/status, and OpenRouter account-wide activity/credits.
OpenRouter panels cover the most recent 30 UTC days plus all-time credit totals.

The five alerts cover low OpenRouter credits and 5-hour/weekly Codex and Claude
quota thresholds. Evaluation errors alert, but `NoData` remains `NoData`; there are
no alerts for exporter collection failure, stale last-success timestamps,
Prometheus disappearance, Grafana disappearance, or whole-VPS loss. Slack recovery
messages are enabled. Alert delivery was not tested during inventory.

The notification-policy root groups by Grafana folder and alert name, uses the
default empty receiver, has no child routes, and does not override Grafana's group
wait, group interval, or repeat interval. Each of the five provisioned rules instead
selects the Slack contact point directly through per-rule notification settings.

## Loki

Loki is a single-process instance with authentication disabled at the application
layer and network access limited to the tailnet/Compose boundary. It uses TSDB
schema v13, R2-compatible object storage, one-year retention, a seven-day
old-sample rejection window, and environment-injected storage credentials.

The service was ready, its local volume was nearly empty, and runtime counters
showed no created ingestion chunks. No log shipper or Loki producer was identified
within the inspected Compose project and user-service boundaries. No ingestion was
observed during inventory, but intermittent or remote producers, cron jobs, Docker
logging drivers, and historical remote objects were not exhaustively ruled out; no
provider call or credential use was authorised.

## Credential and lifecycle findings

Boolean-only inspection confirmed that the effective Compose environment
distributes populated shared credential classes too broadly without emitting any
values:

- Grafana receives provider and object-storage credentials it does not require;
- Loki receives Grafana administration, notification, and provider credentials in
  addition to its required object-storage access;
- the OpenRouter exporter receives Grafana administration and object-storage
  credentials in addition to its required provider credential;
- the stopped Aperture exporter retains unrelated administration and storage
  credential classes.

No values were emitted or exposed to the agent, but container compromise would
have a larger blast radius than intended. Before migration or stack rebuild,
complete a separately reviewed task to split per-service secrets, rotate affected
credentials, recreate only the owned containers, and verify old-credential
rejection. Do not treat deleting environment entries as credential revocation.

Other lifecycle gaps:

- mutable image tags make rebuilds non-reproducible;
- both custom Dockerfiles also use the mutable `python:3.12-slim` base and install
  unpinned Python packages;
- the retained Compose/build snapshot is not deployable without separately managed
  secrets and reviewed runtime ownership;
- the two rate-limit exporters live as enabled user services outside the Compose
  project;
- the Claude collector mutates the interactive CLI credential store during token
  refresh;
- no component has an explicit CPU or PID limit;
- the stopped Aperture container, image, and volume need an explicit later
  retained/removed disposition.

## Migration dependency map

| Current capability | Current dependency | Cloud migration consequence |
| --- | --- | --- |
| Unified usage dashboard | Grafana + Prometheus + four producer paths | Recreate source contracts one at a time; do not retire Prometheus first |
| Codex quota panels | Local user service + `codex app-server` + OTLP | Decide maintained cloud-compatible collection and credential boundary |
| Claude quota panels | Local user service + interactive Claude credential file + OTLP | Replace credential mutation with an approved provider/read boundary |
| Claude session/cost panels | Claude Code OTLP emission | Confirm semantics and whether this local-only telemetry remains required |
| Codex native telemetry | Codex processes + Prometheus OTLP receiver | Filter or exclude; current cardinality is above the proposed cloud ceiling |
| OpenRouter panels | Custom exporter + management credential + Prometheus scrape | Prefer maintained direct Grafana access if source-contract qualification passes |
| Five usage alerts | Grafana evaluator + Prometheus + Slack | Recreate with explicit no-data/stale behavior and externally test delivery |
| Loki | Loki + R2 credentials/bucket | Confirm no historical requirement, then retire separately after qualification |

The OpenRouter exporter makes sequential activity and credit requests with a
30-second timeout and five-minute polling. It implements no pagination, retry,
backoff, or explicit rate-limit handling. On failure it sets the collection-success
gauge to zero but retains the previous activity and credit gauges, so consumers
must use collection success and last-success age rather than interpreting stale
values as current. Issue #6 must qualify these semantics against any direct-cloud
replacement.

The stopped Aperture exporter lists R2 objects, decodes compressed CBOR usage
records, emits identity/model/status/cost/token counters, and persists processed
object names. Identity labels may contain a user tag or login name, creating a
privacy and cardinality boundary. It has no object-list pagination, retry/backoff,
or explicit rate-limit handling. Any decoder exception ends the current file, but
the caller still marks that object processed, creating a partial-file data-loss
risk without a distinct failure state. It is superseded and must not be selected
as a cloud migration source without separate qualification.

## Recovery and retention disposition

The secret-scanned recovery snapshot retains sanitised Compose/build sources plus
declarative dashboard, data-source, alert, Prometheus, Loki, Aperture, and
OpenRouter exporter definitions. It omits credential values, database state, raw
telemetry, logs, provider responses, tailnet addresses, and owner credential files.

Keep the local stack unchanged through parallel cloud qualification. Keep this
snapshot through cutover and the agreed rollback window, then review it alongside
the local-stack retirement task. The stopped Aperture state, custom images, local
volumes, and R2 bucket are not authorised for deletion by this inventory.

## Unverified boundaries

- Grafana alert firing/recovery and Slack delivery were not exercised.
- No Grafana Cloud, provider, Hostinger, Slack, R2, or owner credential was used.
- R2 historical objects and costs were not queried.
- A full Compose rebuild was not tested; the retained reference intentionally lacks
  live secrets and state.
- Dashboard rendering and query correctness were not practically exercised.
- Resource figures are one short sample, not peak or trend evidence.
