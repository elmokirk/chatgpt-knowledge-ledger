# ChatGPT Knowledge Ledger · User Manual

## Choose a mode

| Mode | Use it for | Limitation |
|---|---|---|
| Export ZIP | Complete historical baseline | Requires the email export |
| Guarded recent sync | Ongoing recent changes | The app window is not a historical backup |

Use both: import the export once, then keep recent work current with the guarded sync.

## Set up the vault

```powershell
git clone https://github.com/elmokirk/chatgpt-knowledge-ledger.git
cd chatgpt-knowledge-ledger
python scripts/chatlog.py init --vault "../my-chatgpt-ledger"
python scripts/chatlog.py validate --vault "../my-chatgpt-ledger"
```

Keep the vault private. Never place personal exports or real account identifiers in this repository.

## Import an export

Put the unchanged ZIP in `10 - Ingest/RAW/export.zip`, then run:

```powershell
python scripts/chatlog.py inspect-export --input "../my-chatgpt-ledger/10 - Ingest/RAW/export.zip"
python scripts/chatlog.py ingest-export --input "../my-chatgpt-ledger/10 - Ingest/RAW/export.zip" --vault "../my-chatgpt-ledger"
python scripts/chatlog.py validate --vault "../my-chatgpt-ledger"
```

Review the root note, newest Weekly MOC, Entity Candidates, transcripts, and output records.

## Enable guarded recent sync

1. Create an otherwise unused ChatGPT project in the intended workspace.
2. Obtain the current runtime account ID and that project's stable `g-p-…` ID.
3. Edit the private vault's `09 - System/State/scheduler.config.json`.
4. Set `enabled` to `true`, then insert both identifiers under `identity_guard`.
5. Create a local automation only after the vault owner approves it.

Under `summarization`, choose the model and limits. Defaults are `gpt-6-luna`, `low`, 1000 characters for Chat Notes, and 400 for Weekly MOC rows. Keep full text in transcripts; indexes are summaries only. No summary may exceed the hard 3000-character ceiling.

Every scheduled attempt must run `scheduler-status` first. A completed ISO week stops immediately. A due week must pass both the account-ID and project-ID checks before any chat is listed.

## Agent setup contract

An assisting agent must:

1. Read `AGENTS.md` and this README.
2. Keep reusable code in `development/` and personal data in the explicitly supplied `--vault`.
3. Run `init` and `validate`.
4. Ask the owner to create or select a private sentinel project.
5. Read the runtime account ID and ChatGPT project IDs without reading chats.
6. Store real identifiers only in the private `scheduler.config.json`.
7. Test wrong-account, missing-project, duplicate-week, and lock behavior with synthetic public fixtures.
8. Run public preflight and the complete test suite before committing public changes.
9. Create an automation only with explicit owner authorization.

Identity failure is always fail-closed: no fallback to email, plan type, titles, local folders, or chat content.

## Run records

- Central overview: `09 - System/Registries/Sync Run Registry.json`
- Individual receipts: `09 - System/Runs/<year>/`
- Current automation state: `09 - System/State/Scheduler State.json`
- Active lock: `09 - System/State/Weekly Sync.lock`

Do not delete a stale lock automatically. Inspect the recorded run first.

## Update safely

Back up the private vault, update the public tooling, run `init` against a staging copy, validate it, then update the working vault. `init` preserves existing scheduler configuration and state.
