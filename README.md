# ChatGPT Knowledge Ledger

Turn a ChatGPT data export into a private, Obsidian-compatible knowledge ledger with compact chat notes, full branch-aware transcripts, weekly maps of content, controlled classifications, entity review, and separately tracked large code artifacts.

Your conversations stay in a vault you choose. This repository contains the reusable tooling only.

## Requirements

- Git
- Python 3.11 or newer
- Obsidian is optional

## Five-minute setup

```powershell
git clone https://github.com/elmokirk/chatgpt-knowledge-ledger.git
cd chatgpt-knowledge-ledger
python scripts/chatlog.py init --vault "../my-chatgpt-ledger"
python scripts/chatlog.py validate --vault "../my-chatgpt-ledger"
```

`init` creates the documented ingest directory at `10 - Ingest/RAW`. Paths use native platform separators; the quoted names with spaces are supported on Windows, macOS, and Linux.

Open `../my-chatgpt-ledger/00 - ChatGPT Knowledge Ledger.md` directly or add the folder as an Obsidian vault.

## Import your ChatGPT export

1. In ChatGPT open **Settings → Data Controls → Export data** and confirm the request.
2. Download the ZIP from the email sent by OpenAI. Do not extract or rename it.
3. Put it in `../my-chatgpt-ledger/10 - Ingest/RAW/`.
4. Inspect before importing:

```powershell
python scripts/chatlog.py inspect-export --input "../my-chatgpt-ledger/10 - Ingest/RAW/export.zip"
```

5. Import and validate:

```powershell
python scripts/chatlog.py ingest-export --input "../my-chatgpt-ledger/10 - Ingest/RAW/export.zip" --vault "../my-chatgpt-ledger"
python scripts/chatlog.py validate --vault "../my-chatgpt-ledger"
```

Review the root note, the newest file under `01 - MOCs/Weekly/`, the Entity Candidate Queue, and any records under `04 - Outputs/Records/`.

## Optional guarded recent sync

Create an otherwise unused ChatGPT project in the personal workspace and copy its stable project ID. Configure `09 - System/State/scheduler.config.json` inside the private vault with the expected runtime account ID and that project ID, then set `enabled` to `true`. Never commit this private configuration.

Automations should call `scheduler-status` first. `noop` ends the run without account or chat lookups. When due, read the current runtime account ID and ChatGPT project IDs, then acquire the weekly lock:

```powershell
python scripts/chatlog.py scheduler-status --vault "../my-chatgpt-ledger" --now "2026-09-28T12:00:00+02:00"
python scripts/chatlog.py scheduler-begin --vault "../my-chatgpt-ledger" --now "2026-09-28T12:00:00+02:00" --account-id "observed-account-id" --project-id "g-p-observed-project-id"
```

Missing or mismatched identity signals abort before chat retrieval. A completed ISO week becomes a cheap no-op; failed weeks may retry. `scheduler-finish` writes an immutable receipt under `09 - System/Runs/` and updates `09 - System/Registries/Sync Run Registry.json`.

## Safety model

- RAW evidence and human annotations are never overwritten.
- Existing immutable targets with different bytes stop the operation.
- Unknown entities require review before becoming canonical.
- Asset reconciliation defaults to report-only.
- Extracted code is stored as evidence and never executed.
- No global skills are installed.

## Updating

Use versioned releases. Back up the private vault, test migrations against a staging copy, validate it, and only then replace the working vault.

## Current release status

This is a release candidate until the documented flow succeeds from a fresh GitHub clone with a real user export.
