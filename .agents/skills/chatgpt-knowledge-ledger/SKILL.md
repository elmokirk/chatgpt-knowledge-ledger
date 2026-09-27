---
name: chatgpt-knowledge-ledger
description: Inspect, ingest, render, validate, rebuild, and query the workspace-local ChatGPT Knowledge Ledger.
metadata:
  version: "1.1.0"
---

# ChatGPT Knowledge Ledger

Read the root `AGENTS.md`, then use the smallest mode required. `inspect-export` is read-only. `ingest-export` may only target an explicit workspace vault and must stage/validate before any real-source promotion. Never ingest real exports without run-specific owner authorization.

Modes: `inspect-export`, `ingest-export`, `sync-recent`, `rebuild-indexes`, `validate`, `query`.

Invariants: preserve raw records; key by `chat_id`; retain branches; require `contexts` and `content_types`; queue unknown entities; externalize code exceeding 300 lines or 32 KiB; never overwrite companions; never place unbounded model text in an index; never install this skill globally.

Commands are routed through `scripts/chatlog.py`. Read the matching reference before a mutating mode.

Read [references/summarization.md](references/summarization.md) before rendering chat notes or MOCs.
