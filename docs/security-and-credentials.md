# Security and credential handling

Status: repository governance baseline. This document defines handling boundaries;
it contains no credential values and does not authorise creation of live secrets.

## Repository and roles

- `jwill9999` is the repository owner and sole current administrator. The owner
  controls repository visibility, collaborator access, GitHub environments, cloud
  administration, credential creation, rotation, and revocation.
- Agents may prepare secret-free configuration, identify the exact destination and
  required scope of a credential, and verify behavior that does not reveal its
  value. Agents must not ask the owner to paste credentials into chat, issues,
  logs, screenshots, commits, or command output.
- GitHub Issues owns live task state and compact acceptance evidence. Repository
  documents own reviewed policy, architecture, configuration, and runbooks.
- The repository is public as of 22 November 2026. Treat all tracked content and
  GitHub discussion as public. Returning it to private is an owner decision after
  confirming that required ruleset and security features remain available; making
  it private is not a substitute for removing or rotating exposed secrets.

## Enforced change boundary

The default branch is `main`. The active `Main` ruleset targets the default branch,
has no bypass actors, requires pull requests and resolved review conversations,
dismisses stale reviews after new pushes, and blocks deletion and non-fast-forward
updates. Zero approving reviews are currently required because the owner is the
only collaborator. A second trusted reviewer should be added before increasing the
required approval count; until then, substantial security, lifecycle, and
migration changes require an independent read-only critique recorded in the pull
request or owning issue.

Third-party Actions must be pinned to immutable commit SHAs and receive only the
permissions they need. Branch protection, CI, and secret scanning are safeguards,
not permission to commit credentials.

The initial validation workflow uses these reviewed dependencies:

- `actions/checkout` release `v7.0.1`, pinned to upstream commit
  `3d3c42e5aac5ba805825da76410c181273ba90b1`, performs the Git checkout. It
  receives only repository `contents: read` through the workflow token.
- `gitleaks/gitleaks-action` release `v3.0.0`, pinned to upstream commit
  `e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e`, scans complete Git history. The
  personal-account repository needs no Gitleaks licence. PR comments and scan
  artefact upload are disabled; the workflow token has only `contents: read`.

The release tags and commits were resolved from their upstream GitHub repositories
on 22 November 2026. Updating either pin requires repeating the source, release,
runtime, permission, and data-exposure review. Complete history is supplied to
Gitleaks intentionally because deleting a secret in a later commit does not remove
the exposure.

## Credential classes and destinations

| Class | Minimum scope | Authoritative destination | Prohibited destinations |
| --- | --- | --- | --- |
| Grafana administration | Named human administrator; MFA; no routine collector use | Owner-managed Grafana Cloud account | Git, chat, VPS environment files, dashboards |
| Telemetry write | Write only to the intended Grafana Cloud stack/tenant | Root-owned `0600` VPS environment file or maintained container-secret mechanism | Alloy configuration, images, GitHub issues, logs |
| Provider usage read | Read-only usage/billing scope for one provider and organisation where supported | Grafana Cloud secure data-source field | Dashboard JSON, query text, Git, VPS exporter unless separately approved |
| Notification delivery | Send only through the selected contact point | Grafana Cloud secure contact-point field or provider secret store | Alert annotations, exported rules, Git, chat |
| GitHub runner | Repository-scoped registration/ephemeral identity; no signing authority | GitHub runner registration flow and Mac keychain/runner service boundary | Workflow files, runner worktree, logs, owner checkout |
| Apple signing/notarisation | Narrow certificate/profile/API role for an explicitly approved release workflow | Mac keychain and GitHub environment secrets with owner approval | VPS, general runner environment, artefacts, Git, chat |
| Hostinger administration | Named human administrator; MFA; recovery access | Owner-managed Hostinger account/password manager | VPS files, Grafana, GitHub Actions, chat |

Use separate identities across classes. Do not reuse an administration credential
for telemetry, provider reads, notifications, runners, or signing. If a provider
cannot supply the stated least privilege, record the exact residual access and get
owner approval before creating the credential.

## Owner-operated creation and handoff

1. The implementation task records the credential class, exact minimum scope,
   destination, owner, expiry/rotation trigger, and revocation path without a value.
2. The owner creates the credential directly in the provider UI or supported CLI
   from a trusted device. MFA and a password manager protect human administration.
3. The owner enters the value directly into the authoritative destination. Do not
   relay it through an agent, clipboard transcript, issue, pull request, terminal
   output, or screenshot.
4. Verification exposes only a pass/fail result, credential identifier suffix if
   safe, creation date, and scope. Commands must not echo environment variables or
   dump configuration containing secure fields.
5. Record the owner, destination, scope, rotation trigger, and successful test in
   the owning issue. Never record the value.

## Rotation and revocation

- Rotate on provider requirement, scope change, personnel/access change, suspected
  disclosure, unexpected authentication use, or before an agreed expiry.
- Prefer overlap: create a replacement, place it in the destination, perform one
  bounded verification, then revoke the old credential. If exposure is suspected,
  revoke first when continued access is the greater risk.
- After revocation, verify that the old credential fails and the replacement works,
  then check dashboards, alerts, collectors, and runner jobs for authentication
  errors. Remove obsolete secret versions and local temporary material.
- Signing credentials require a separate owner-approved release runbook and must
  not be introduced as part of observability migration.

Human-account MFA recovery codes and break-glass material belong in the owner's
password manager or offline recovery store, never Git, chat, the VPS, Grafana, or
runner workspaces. The owner should periodically verify recovery access without
exposing the material and rotate recovery material after use or suspected access.

## Suspected exposure response

1. Stop copying, displaying, or investigating the value. Preserve only safe
   metadata such as affected system, time, path, and credential class.
2. Notify the owner privately without including the value.
3. Revoke or rotate at the source of truth. Disabling a file or deleting a message
   does not invalidate a credential.
4. Remove the value from its unauthorised destination. If committed, assume Git
   history, forks, caches, logs, and telemetry may retain it; history rewriting is
   a separately approved containment step, never the primary remediation.
5. Review provider audit logs and affected access during the exposure window.
6. Verify replacement operation and old-credential rejection, then record a
   redacted incident disposition and any control change.

## Evidence and retention

Keep only secret-free configuration, compact test outcomes, source revisions,
reviewed rollback instructions, and ownership metadata. Do not retain raw provider
responses, telemetry exports, prompts, logs, VM disks, signed artefacts, or
credential-bearing screenshots in GitHub. Task-owned disposable evidence must have
an explicit location, owner, expiry, and cleanup verification.
