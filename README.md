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
