"""Create/update static demo-vault contracts, policies, templates, and configuration."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "work" / "chatgpt-knowledge-ledger-demo"

ENUMS = {
    "session_kind": ["build", "research", "strategy_sales", "system_skill", "personal", "administrative", "mixed", "unknown"],
    "source_kind": ["chatgpt_export", "chatgpt_live_index", "hybrid"],
    "workflow_status": ["completed", "partial", "blocked", "exploratory", "abandoned", "unknown"],
    "completeness": ["full", "partial", "metadata_only"],
    "privacy_class": ["private", "sensitive", "restricted"],
    "verification_status": ["verified", "runtime_verified", "static_only", "claimed", "not_verified", "not_applicable", "unknown"],
    "chat_url_status": ["verified", "unverified", "unavailable"],
    "contexts": ["personal", "business", "project", "administration", "learning", "mixed", "unknown"],
    "content_types": ["review", "reflection", "planning", "research", "implementation", "debugging", "strategy", "writing", "ideation", "decision_making", "administration", "learning", "mixed", "unknown"],
    "candidate_status": ["pending", "approved", "rejected", "merged"],
    "entity_axis": ["area", "project", "concept", "collection", "person"],
}

def obj_schema(schema_id: str, note_type: str, required: list[str], props: dict) -> dict:
    base = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "type": "object",
        "additionalProperties": False,
        "required": ["schema", "note_type", *required],
        "properties": {"schema": {"const": schema_id}, "note_type": {"const": note_type}, **props},
    }
    return base

str_t = {"type": "string"}
timestamp = {"type": "string", "format": "date-time"}
string_list = {"type": "array", "items": {"type": "string"}, "uniqueItems": True}

SCHEMAS = {
    "chat-session.schema.json": obj_schema("chatgpt-session/v2", "chat_session", ["session_kind", "note_id", "chat_id", "title", "created_at", "updated_at", "indexed_at", "source_kind", "primary_goal", "summary", "workflow_status", "completeness", "privacy_class", "contexts", "content_types"], {
        "session_kind": {"enum": ENUMS["session_kind"]}, "note_id": str_t, "chat_id": str_t, "title": str_t,
        "created_at": timestamp, "updated_at": timestamp, "indexed_at": timestamp, "source_kind": {"enum": ENUMS["source_kind"]},
        "source_batch_id": str_t, "source_record": str_t, "parser_version": str_t, "chat_url": str_t,
        "chat_url_status": {"enum": ENUMS["chat_url_status"]}, "chat_url_checked_at": {"type": ["string", "null"]}, "share_url": str_t,
        "primary_goal": str_t, "summary": str_t, "workflow_status": {"enum": ENUMS["workflow_status"]}, "completeness": {"enum": ENUMS["completeness"]},
        "privacy_class": {"enum": ENUMS["privacy_class"]}, "verification_status": {"enum": ENUMS["verification_status"]},
        "areas": string_list, "projects": string_list, "concepts": string_list, "collections": string_list, "people": string_list,
        "contexts": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"enum": ENUMS["contexts"]}},
        "content_types": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"enum": ENUMS["content_types"]}},
        "topics": string_list, "output_types": string_list, "output_refs": string_list, "asset_refs": string_list, "source_refs": string_list,
        "weekly_moc": str_t, "raw_transcript": str_t, "normalized_transcript": str_t, "annotation_ref": str_t,
        "turn_count": {"type": "integer", "minimum": 0}, "branch_count": {"type": "integer", "minimum": 1}, "asset_count": {"type": "integer", "minimum": 0}, "source_count": {"type": "integer", "minimum": 0},
        "has_full_transcript": {"type": "boolean"}, "has_branches": {"type": "boolean"}, "has_assets": {"type": "boolean"}, "has_open_loops": {"type": "boolean"}, "has_annotation": {"type": "boolean"}
    }),
    "transcript.schema.json": obj_schema("chatgpt-transcript/v2", "normalized_transcript", ["chat_id", "branch_id", "message_count", "parser_version", "code_storage"], {
        "chat_id": str_t, "branch_id": str_t, "parent_message_id": {"type": ["string", "null"]}, "message_count": {"type": "integer", "minimum": 0},
        "parser_version": str_t,
        "code_storage": {"enum": ["inline", "mixed", "externalized"]}, "externalized_code_refs": string_list
    }),
    "output-record.schema.json": obj_schema("chatgpt-output/v2", "output_record", ["output_id", "title", "output_type", "origin_chat_ids", "contexts", "content_types", "verification_status"], {
        "output_id": str_t, "title": str_t, "output_type": str_t, "origin_chat_ids": {"type": "array", "minItems": 1, "items": str_t},
        "origin_message_id": str_t, "origin_branch_id": str_t, "block_ordinal": {"type": "integer", "minimum": 1},
        "contexts": {"type": "array", "minItems": 1, "items": {"enum": ENUMS["contexts"]}}, "content_types": {"type": "array", "minItems": 1, "items": {"enum": ENUMS["content_types"]}},
        "projects": string_list, "topics": string_list, "language": str_t, "file_extension": str_t, "line_count": {"type": "integer"}, "byte_count": {"type": "integer"},
        "extraction_rule": {"enum": ["line_threshold", "byte_threshold", "explicit"]},
        "local_file": str_t, "source_transcript": str_t, "source_anchor": str_t, "verification_status": {"enum": ENUMS["verification_status"]}
    }),
    "asset-record.schema.json": obj_schema("chatgpt-asset/v2", "asset_record", ["asset_id", "title", "asset_kind", "origin_chat_ids", "resolution_status", "match_state", "match_method", "privacy_class"], {
        "asset_id": str_t, "title": str_t, "asset_kind": {"enum": ["input_attachment", "generated_asset", "external_output", "audio", "image", "video", "archive", "document", "code", "unknown_reference"]},
        "origin_chat_ids": string_list, "origin_message_ids": string_list, "output_refs": string_list, "mime_type": str_t, "original_filename": str_t, "original_url": str_t,
        "origin_path": str_t, "local_path": str_t, "file_size": {"type": "integer", "minimum": 0},
        "resolution_status": {"enum": ["referenced_only", "download_candidate", "staged", "local_verified", "missing", "inaccessible", "quarantined"]},
        "match_state": {"enum": ["verified", "high_confidence", "ambiguous", "unmatched", "rejected"]},
        "match_method": {"enum": ["source_id", "exact_bytes", "explicit_filename", "explicit_filename_and_unique_time_window", "manual", "suggested"]},
        "discovered_at": timestamp, "moved_at": {"type": ["string", "null"]}, "privacy_class": {"enum": ENUMS["privacy_class"]},
        "operation_kind": {"enum": ["report_only", "move", "deduplicate"]}, "source_cleanup_status": {"enum": ["not_applicable", "pending", "verified", "failed"]},
        "duplicate_disposition": {"enum": ["none", "retained_pilot", "recycle_bin", "existing_payload_reused"]}, "recycle_receipt": str_t
    }),
    "source-record.schema.json": obj_schema("chatgpt-source/v1", "source_record", ["source_id", "title", "url", "first_seen_at", "origin_chat_ids", "evidence_status"], {
        "source_id": str_t, "title": str_t, "url": {"type": "string", "format": "uri"}, "publisher": str_t, "first_seen_at": timestamp,
        "origin_chat_ids": string_list, "purpose": str_t, "evidence_status": {"enum": ["verified", "claimed", "unverified", "unavailable"]}, "local_snapshot": str_t
    }),
    "annotation-companion.schema.json": obj_schema("chatgpt-annotation/v1", "chat_annotation", ["annotation_id", "chat_id", "chat_note", "created_at", "updated_at", "annotation_status", "annotation_kinds", "author"], {
        "annotation_id": str_t, "chat_id": str_t, "chat_note": str_t, "created_at": timestamp, "updated_at": timestamp,
        "annotation_status": {"enum": ["active", "superseded"]}, "annotation_kinds": string_list, "author": str_t
    }),
    "ingest-run.schema.json": obj_schema("chatgpt-ingest-run/v2", "ingest_run", ["run_id", "mode", "started_at", "status", "parser_version", "schema_version", "source_file", "source_bytes"], {
        "run_id": str_t, "mode": {"enum": ["inspect_export", "ingest_export", "sync_recent", "rebuild_indexes", "validate", "asset_reconcile"]},
        "started_at": timestamp, "completed_at": {"type": ["string", "null"]}, "status": {"enum": ["running", "completed", "partial", "failed"]},
        "parser_version": str_t, "schema_version": str_t, "source_file": str_t, "source_bytes": {"type": "integer", "minimum": 0}, "counts": {"type": "object"}, "warnings": string_list, "errors": string_list
    }),
    "weekly-moc.schema.json": obj_schema("chatgpt-weekly-moc/v1", "weekly_moc", ["iso_week", "period_start", "period_end", "generated_at", "run_id", "chat_count", "new_count", "updated_count", "output_count", "asset_count", "source_count", "entity_candidate_count", "coverage_status"], {
        "iso_week": {"type": "string", "pattern": "^[0-9]{4}-W[0-9]{2}$"}, "period_start": str_t, "period_end": str_t, "generated_at": timestamp, "run_id": str_t,
        "chat_count": {"type": "integer"}, "new_count": {"type": "integer"}, "updated_count": {"type": "integer"}, "output_count": {"type": "integer"}, "asset_count": {"type": "integer"}, "source_count": {"type": "integer"}, "entity_candidate_count": {"type": "integer"}, "coverage_status": {"enum": ["complete", "risk", "partial"]}
    }),
}

CORE_HEADINGS = """## Abstract\n\n> [!abstract] Abstract\n> {{abstract}}\n\n## Navigation\n\n- [[#Intent and success criteria|Intent and success criteria]]\n- [[#Outcomes|Outcomes]]\n- [[#Outputs and assets|Outputs and assets]]\n- [[#Open loops and next actions|Open loops and next actions]]\n- [[#Transcript references|Transcript references]]\n\n## Intent and success criteria\n\n- **Primary goal:** {{primary_goal}}\n- **Requested deliverable:** {{requested_deliverable}}\n- **Success criteria:** {{success_criteria}}\n\n## Starting context and inputs\n\n{{inputs}}\n\n## Outcomes\n\n{{outcomes}}\n\n## Decisions\n\n{{decisions}}\n\n## Iterations and feedback\n\n{{iterations}}\n\n## Outputs and assets\n\n{{outputs}}\n\n## Verification and evidence\n\n{{verification}}\n\n## Research and sources\n\n{{sources}}\n\n## Failures and blockers\n\n{{failures}}\n\n## Open loops and next actions\n\n{{open_loops}}\n\n## Reuse and transferability\n\n{{reuse}}\n\n## Related knowledge\n\n{{related}}\n\n## Transcript references\n\n{{transcript_refs}}\n"""

TEMPLATES = {
    "Chat Session - Core.md": "---\nschema: chatgpt-session/v2\nnote_type: chat_session\ncontexts: []\ncontent_types: []\n---\n\n# {{title}}\n\n" + CORE_HEADINGS,
    "Chat Session - Build.md": "---\ntemplate: chat-session-build\n---\n\n" + CORE_HEADINGS + "\n## Architecture\n\n{{architecture}}\n\n## Implementation details\n\n{{implementation}}\n\n## Dependencies\n\n{{dependencies}}\n\n## Test matrix\n\n{{tests}}\n\n## Deployment state\n\n{{deployment}}\n",
    "Chat Session - Research.md": "---\ntemplate: chat-session-research\n---\n\n" + CORE_HEADINGS + "\n## Research questions\n\n{{questions}}\n\n## Findings\n\n{{findings}}\n\n## Evidence quality\n\n{{evidence_quality}}\n\n## Contradictions\n\n{{contradictions}}\n\n## Freshness\n\n{{freshness}}\n",
    "Chat Session - Strategy and Sales.md": "---\ntemplate: chat-session-strategy-sales\n---\n\n" + CORE_HEADINGS + "\n## Audience\n\n{{audience}}\n\n## Offer and pricing\n\n{{offer}}\n\n## Scripts and objections\n\n{{scripts}}\n\n## Follow-up state\n\n{{follow_up}}\n",
    "Chat Session - System and Skill.md": "---\ntemplate: chat-session-system-skill\n---\n\n" + CORE_HEADINGS + "\n## Contracts and interfaces\n\n{{contracts}}\n\n## Invariants\n\n{{invariants}}\n\n## Release artifact\n\n{{release}}\n\n## Migration notes\n\n{{migration}}\n",
    "Chat Session - Personal.md": "---\ntemplate: chat-session-personal\nprivacy_class: sensitive\n---\n\n" + CORE_HEADINGS + "\n## Hypotheses and reflection\n\n{{reflection}}\n\n## Commitments\n\n{{commitments}}\n",
    "Chat Session - Administrative.md": "---\ntemplate: chat-session-administrative\nprivacy_class: sensitive\n---\n\n" + CORE_HEADINGS + "\n## Authority and documents\n\n{{authority}}\n\n## Deadlines and submission state\n\n{{submission}}\n",
    "Chat Annotation Companion.md": "---\nschema: chatgpt-annotation/v1\nnote_type: chat_annotation\n---\n\n# {{title}} · Annotations\n\n## Human summary\n\n## Corrections and clarifications\n\n## Decisions after the chat\n\n## Reuse notes\n\n## Follow-ups\n",
    "Weekly MOC.md": "---\nschema: chatgpt-weekly-moc/v1\nnote_type: weekly_moc\n---\n\n# ChatGPT Weekly MOC · {{iso_week}}\n\n## Chat overview\n\n| Created | Updated | Chat | What was done | Context | Content types | Projects | ChatGPT | Chat note | Human note | Outputs | Status |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n{{chat_rows}}\n\n## Outputs created or updated\n\n{{outputs}}\n\n## Assets reconciled\n\n{{assets}}\n\n## Research sources registered\n\n{{sources}}\n\n## Open loops\n\n{{open_loops}}\n\n## Entity candidates requiring review\n\n{{entity_candidates}}\n\n## Run health\n\n{{run_health}}\n",
    "Project MOC.md": "---\nnote_type: project_moc\nentity_id: {{entity_id}}\n---\n\n# {{title}}\n\n## Chats\n\n{{chats}}\n\n## Outputs\n\n{{outputs}}\n",
    "Concept MOC.md": "---\nnote_type: concept_moc\nentity_id: {{entity_id}}\n---\n\n# {{title}}\n\n## Definition\n\n{{definition}}\n\n## Chats\n\n{{chats}}\n",
    "Collection MOC.md": "---\nnote_type: collection_moc\nentity_id: {{entity_id}}\n---\n\n# {{title}}\n\n## Members\n\n{{members}}\n",
    "Area MOC.md": "---\nnote_type: area_moc\nentity_id: {{entity_id}}\n---\n\n# {{title}}\n\n## Active work\n\n{{work}}\n",
    "Entity MOC.md": "---\nnote_type: entity_moc\nentity_axis: {{entity_axis}}\nentity_id: {{entity_id}}\naliases: []\n---\n\n# {{title}}\n\n## Related chats\n\n{{chats}}\n",
    "Normalized Transcript.md": "---\nschema: chatgpt-transcript/v2\nnote_type: normalized_transcript\n---\n\n# Transcript · {{title}}\n\n{{turns}}\n",
    "Output Record.md": "---\nschema: chatgpt-output/v2\nnote_type: output_record\ncontexts: []\ncontent_types: []\n---\n\n# {{title}}\n\n## Provenance\n\n{{provenance}}\n",
    "Code Artifact.md": "---\nschema: chatgpt-output/v2\nnote_type: output_record\noutput_type: code_block\n---\n\n# {{title}}\n\n- Source: {{source_transcript}}#{{source_anchor}}\n- File: {{local_file}}\n",
    "Asset Record.md": "---\nschema: chatgpt-asset/v2\nnote_type: asset_record\n---\n\n# {{title}}\n\n## Provenance and reconciliation\n\n{{provenance}}\n",
    "Source Record.md": "---\nschema: chatgpt-source/v1\nnote_type: source_record\n---\n\n# {{title}}\n\n{{purpose}}\n",
}

DOCS = {
    "Agents/Architecture.md": "# Architecture\n\nThe frozen 0.4.0 design is a layered evidence system: root/index views, MOCs, compact notes, selected transcript evidence, explicit artifact records, then raw source. Canonical ownership and stable IDs prevent duplicated facts.\n",
    "Agents/Retrieval Protocol.md": "# Retrieval Protocol\n\nTranslate the question into typed filters. Read the narrowest MOC/Base, then candidate frontmatter and abstract. Check a companion when present. Escalate only to a required H2, branch transcript, Level-4 record, and finally raw JSON. Distinguish generated interpretation, human correction, and exact evidence.\n",
    "Agents/Classification Policy.md": "# Classification Policy\n\n`contexts` describes the life/work lens and `content_types` the intellectual activity; both are mandatory controlled lists. Entity axes are path-qualified wikilinks. Unknown entities enter the central candidate queue and require approval. Plain vocabulary uses lowercase kebab-case.\n",
    "Agents/Asset Safety Policy.md": "# Asset Safety Policy\n\nDefault to `report_only`. Validate literal roots and explicit files, hash before matching, never execute candidates, never auto-move ambiguous or unsafe types, never permanently delete, and write move plus rollback receipts before registry claims. Real Downloads access requires explicit authorization.\n",
    "Agents/Extension Guide.md": "# Extension Guide\n\nNew properties require a versioned schema, migration, fixtures, renderer change, and documentation. New entity axes require a registry namespace, MOC template, link rules, candidate handling, and retrieval tests. Runtime adapters remain workspace-local and are derived from `.agents/`.\n",
    "Agents/SOPs/Historic Export Ingest.md": "# Historic Export Ingest\n\nPlace an authorized export in `10 - Ingest/RAW`, inspect first, hash and stage, parse branches, validate staged results, atomically promote, then move the immutable ZIP into its processed batch with manifest and receipt. Failures leave the ZIP in RAW.\n",
    "Agents/SOPs/Weekly Delta Sync.md": "# Weekly Delta Sync\n\nLoad at most 50 app entries, keep only ChatGPT chats, deduplicate, enforce overlap and the 50-item coverage guard, upsert changed IDs, rebuild affected views, validate, report, and stay quiet on clean no-op.\n",
    "Agents/SOPs/Asset Reconciliation.md": "# Asset Reconciliation\n\nRun scan, match, and plan-moves in report-only mode. Production move requires an approved literal source root and an exact byte match. Verify destination bytes and rollback receipt before updating canonical state.\n",
    "Agents/SOPs/Query and Evidence Escalation.md": "# Query and Evidence Escalation\n\nUse the retrieval ladder in `Agents/Retrieval Protocol.md`; do not open full transcripts by default. Cite local evidence and the private ChatGPT convenience URL when useful.\n",
    "Agents/SOPs/Schema Migration.md": "# Schema Migration\n\nDocument the reason and compatibility boundary, create a new schema identifier, add migration code and positive/negative fixtures, stage migrated records, validate records and links, and preserve raw evidence plus human companions.\n",
}

BASES = {
    "ChatGPT Chats.base": "filters:\n  and:\n    - note.note_type == \"chat_session\"\nviews:\n  - type: table\n    name: Chats\n    order: [created_at, title, contexts, content_types, projects, workflow_status]\n",
    "ChatGPT Outputs.base": "filters:\n  and:\n    - note.note_type == \"output_record\"\nviews:\n  - type: table\n    name: Outputs\n    order: [title, output_type, contexts, content_types, verification_status]\n",
    "ChatGPT Assets.base": "filters:\n  and:\n    - note.note_type == \"asset_record\"\nviews:\n  - type: table\n    name: Assets\n    order: [title, asset_kind, match_state, resolution_status]\n",
    "ChatGPT Sources.base": "filters:\n  and:\n    - note.note_type == \"source_record\"\nviews:\n  - type: table\n    name: Sources\n    order: [title, publisher, evidence_status]\n",
    "Open Loops.base": "filters:\n  and:\n    - note.note_type == \"chat_session\"\n    - has_open_loops == true\nviews:\n  - type: table\n    name: Open loops\n    order: [updated_at, title, contexts, projects]\n",
    "Ingest Health.base": "filters:\n  or:\n    - completeness != \"full\"\n    - verification_status == \"not_verified\"\nviews:\n  - type: table\n    name: Health\n    order: [updated_at, title, completeness, verification_status]\n",
}

ROOT_MOC = """# ChatGPT Knowledge Ledger

Private, local evidence ledger. Start with the narrowest index and escalate only as needed.

## Navigation

- [[01 - MOCs/Weekly|Weekly MOCs]]
- [[01 - MOCs/Projects|Projects]]
- [[01 - MOCs/Concepts|Concepts]]
- [[01 - MOCs/Collections|Collections]]
- [[01 - MOCs/Areas|Areas]]
- [[07 - Bases/Open Loops.base|Open loops]]
- [[07 - Bases/ChatGPT Outputs.base|Outputs]]
- [[07 - Bases/ChatGPT Assets.base|Assets]]
- [[Agents/Retrieval Protocol|Agent retrieval protocol]]

Raw evidence is immutable. Generated notes are replaceable. Human annotations are optional companion notes and are never overwritten by ingestion.
"""

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.replace("\r\n", "\n")
    if not path.exists() or path.read_text(encoding="utf-8") != data:
        path.write_text(data, encoding="utf-8", newline="\n")

def write_once(path: Path, text: str) -> None:
    if not path.exists(): write(path, text)

def scaffold(vault: Path) -> None:
    global VAULT
    VAULT = vault
    (VAULT / "10 - Ingest" / "RAW").mkdir(parents=True, exist_ok=True)
    for name, schema in SCHEMAS.items():
        write(VAULT / "09 - System" / "Contracts" / name, json.dumps(schema, ensure_ascii=False, indent=2) + "\n")
    vocab = "version: 1.0.0\n" + "\n".join(f"{key}:\n" + "\n".join(f"  - {v}" for v in values) for key, values in ENUMS.items()) + "\n"
    write(VAULT / "09 - System" / "Registries" / "Controlled Vocabularies.yaml", vocab)
    write(VAULT / "09 - System" / "Registries" / "Entity Candidates.yaml", "schema: entity-candidates/v1\nreview_threshold: 10\ncandidates: []\n")
    for name in ("Chat Registry.json", "Asset Registry.json", "Source Registry.json"):
        write(VAULT / "09 - System" / "Registries" / name, json.dumps({"schema": "registry/v1", "records": {}}, indent=2) + "\n")
    write(VAULT / "09 - System" / "State" / "Import State.json", json.dumps({"schema": "import-state/v1", "batches": {}, "last_successful_run": None}, indent=2) + "\n")
    write_once(VAULT / "09 - System" / "State" / "Scheduler State.json", json.dumps({"schema": "scheduler-state/v1", "automation_id": None, "status": "not_created", "observed_successful_runs": 0}, indent=2) + "\n")
    scheduler = {"schema": "chatgpt-scheduler-config/v3", "enabled": False, "create_automation": False, "name": "ChatGPT Knowledge Ledger · Weekly Sync", "timezone": "Europe/Berlin", "cadence": {"frequency": "daily", "interval_days": 2, "hour": 12, "minute": 0, "maximum_successful_runs_per_iso_week": 1}, "identity_guard": {"expected_account_id": "", "required_chatgpt_project_ids": [], "policy": "all", "on_missing_signal": "abort", "on_mismatch": "abort"}, "summarization": {"model": "gpt-6-luna", "reasoning_effort": "low", "chat_max_chars": 1000, "chat_max_sentences": 10, "moc_max_chars": 400, "moc_max_sentences": 3}, "coverage_limit": 50, "notification_policy": "meaningful_changes_only", "downloads_mode": "report_only"}
    write_once(VAULT / "09 - System" / "State" / "scheduler.config.json", json.dumps(scheduler, ensure_ascii=False, indent=2) + "\n")
    write_once(VAULT / "09 - System" / "Registries" / "Sync Run Registry.json", json.dumps({"schema": "chatgpt-sync-run-registry/v1", "last_successful_run": None, "weeks": {}}, indent=2) + "\n")
    for name, content in TEMPLATES.items(): write(VAULT / "08 - Templates" / name, content)
    for rel, content in DOCS.items(): write(VAULT / rel, content)
    for name, content in BASES.items(): write(VAULT / "07 - Bases" / name, content)
    for axis in ("Weekly", "Projects", "Concepts", "Collections", "Areas"):
        write(VAULT / "01 - MOCs" / axis / "Index.md", f"# {axis}\n\nCanonical {axis.lower()} are created only after review.\n")
    write(VAULT / "00 - ChatGPT Knowledge Ledger.md", ROOT_MOC)

def main() -> None:
    scaffold(VAULT)

if __name__ == "__main__": main()
