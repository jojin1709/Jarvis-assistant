# Production Platform Finalization

This layer turns Jarvis into a local-first production platform with optional user-owned cloud sync, privacy-respecting telemetry, release security, remote-worker readiness, and generated documentation.

## Cloud Sync

Cloud sync lives in `backend/sync/` and remains disabled unless the user configures a provider and grants consent.

Supported providers:

- Google Drive using the `drive.file` OAuth scope
- Dropbox using app-folder upload APIs
- OneDrive using Microsoft Graph app-folder APIs

Jarvis creates encrypted `.jvbackup` bundles before upload. The sync allowlist includes workflows, memory exports, skills, plugins, and safe configs. It excludes raw browser profiles, cookies, `.env` files, virtual environments, node modules, provider key stores, and other local secrets.

The recommended remote layout is:

```text
Jarvis/
  workflows/
  memory/
  skills/
  plugins/
  backups/
  configs/
```

## Optimization

Runtime optimization lives in `backend/optimization/`:

- memory pressure detection and garbage collection
- browser lease pooling metadata
- agent priority scheduling
- GPU assignment planning
- async runtime throttling
- workflow graph optimization
- execution profiling

These services feed `/api/optimization/status` and the dashboard production runtime panel.

## Testing

The test tree now includes enterprise test lanes:

```text
backend/tests/
  integration/
  workflows/
  browser/
  updater/
  recovery/
  agents/
  installer/
  performance/
```

Core coverage includes sync encryption, conflict resolution, telemetry defaults, release manifest validation, safety governance, dry-run behavior, provider routing, workflow validation, cognition, memory, and planning.

## Release Workflow

Release security lives in `backend/release_security/`.

Build:

```powershell
npm run build
```

Package:

```powershell
npm run pack
```

Windows installer:

```powershell
npm run dist
```

Optional signing uses:

```powershell
$env:JX_JARVIS_SIGNING_CERT_PATH="C:\path\to\cert.pfx"
$env:JX_JARVIS_TIMESTAMP_SERVER="http://timestamp.digicert.com"
```

Jarvis can generate the `signtool` command and validate release artifacts with SHA-256 hashes before update installation.

## Installer And Update Lifecycle

1. Build frontend assets.
2. Bundle backend modules through Electron `extraResources`.
3. Build backend distribution.
4. Package with Electron Builder.
5. Optionally sign the executable.
6. Publish update manifest with SHA-256.
7. Verify update manifest and downloaded artifact before install.

## Privacy And Telemetry

Telemetry lives in `backend/telemetry/` and is disabled by default. Diagnostics remain local unless the user explicitly enables sharing. Legal and consent controls live in `backend/legal/`.
