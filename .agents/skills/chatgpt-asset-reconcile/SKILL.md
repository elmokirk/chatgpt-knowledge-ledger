---
name: chatgpt-asset-reconcile
description: Safely inventory, match, plan, move, validate, and roll back explicitly configured asset candidates.
metadata:
  version: "1.0.0"
---

# ChatGPT Asset Reconcile

Read root `AGENTS.md` and `Agents/Asset Safety Policy.md`. Default to `report_only`. A real Downloads root is never implicit and requires explicit run authorization. Resolve literal roots, enumerate explicit files, hash before matching, and write a manifest.

Only an approved Tier A source-identity or exact-byte match may move in production. Unsafe, executable, archive, script, source-code, macro-enabled, unknown, fuzzy, or ambiguous candidates never auto-move or execute. Verify destination bytes and record rollback before updating canonical state. Never permanently delete and never install this skill globally.
