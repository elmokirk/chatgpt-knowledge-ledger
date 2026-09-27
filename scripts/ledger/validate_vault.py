from __future__ import annotations

import json, re
from pathlib import Path
from .contracts import schema_for, validate, ValidationError
from .util import parse_frontmatter

SCHEMA_FILES={"chatgpt-session/v2":"chat-session.schema.json","chatgpt-transcript/v2":"transcript.schema.json","chatgpt-output/v2":"output-record.schema.json","chatgpt-asset/v2":"asset-record.schema.json","chatgpt-source/v1":"source-record.schema.json","chatgpt-annotation/v1":"annotation-companion.schema.json","chatgpt-ingest-run/v2":"ingest-run.schema.json","chatgpt-weekly-moc/v1":"weekly-moc.schema.json"}
WIKILINK=re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
LEDGER_ROOTS={"00 - ChatGPT Knowledge Ledger.md","01 - MOCs","02 - Chats","02A - Annotations","03 - Transcripts","04 - Outputs","05 - Assets","06 - Sources","07 - Bases","08 - Templates","09 - System","10 - Ingest","Agents"}

def validate_vault(vault: Path) -> dict:
    errors=[]; validated=links=0
    for path in sorted(vault.rglob("*.md")):
        if "08 - Templates" in path.parts:
            continue
        text=path.read_text(encoding="utf-8")
        if text.startswith("---\n"):
            try:
                meta=parse_frontmatter(text); sid=meta.get("schema")
                if sid in SCHEMA_FILES: validate(meta,schema_for(vault,SCHEMA_FILES[sid]),str(path.relative_to(vault))); validated+=1
            except (ValueError,ValidationError) as exc: errors.append(str(exc))
        for target in WIKILINK.findall(text):
            if target.replace("\\","/").split("/",1)[0] not in LEDGER_ROOTS:
                continue
            links+=1; candidate=vault/target
            options=[candidate,candidate.with_suffix(".md"),candidate.with_suffix(".base"),candidate.with_suffix(".json"),candidate.with_suffix(".yaml")]
            if not any(x.exists() for x in options): errors.append(f"unresolved link: {path.relative_to(vault)} -> {target}")
    global_markers=["/.codex/skills","\\.codex\\skills","~/.codex","~/.claude"]
    manifest=(vault.parents[1]/".agents"/"runtime-manifest.json")
    if manifest.exists():
        raw=manifest.read_text(encoding="utf-8")
        if any(x in raw for x in global_markers): errors.append("runtime manifest contains global target")
    return {"ok":not errors,"validated_records":validated,"checked_links":links,"errors":errors}
