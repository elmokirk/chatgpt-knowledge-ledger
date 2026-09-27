from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from .contracts import schema_for, validate
from .util import atomic_write, dump_frontmatter

def markdown_escape(value): return str(value).replace("|","\\|").replace("\n"," ")

def render_weekly(vault: Path, records: list[dict], run_id="run_fixture", generated_at="2026-09-12T12:00:00+02:00", candidates=None) -> Path:
    candidates=candidates or []
    if records:
        d=datetime.fromisoformat(records[0]["metadata"]["created_at"]).date()
    else: d=date.fromisoformat(generated_at[:10])
    year,week,_=d.isocalendar(); start=d-timedelta(days=d.weekday()); end=start+timedelta(days=6); iso_week=f"{year}-W{week:02d}"
    rel=Path("01 - MOCs")/"Weekly"/str(year)/f"{iso_week} - ChatGPT Weekly MOC.md"
    meta={"schema":"chatgpt-weekly-moc/v1","note_type":"weekly_moc","iso_week":iso_week,"period_start":start.isoformat(),"period_end":end.isoformat(),"generated_at":generated_at,"run_id":run_id,"chat_count":len(records),"new_count":len(records),"updated_count":0,"output_count":sum(len(r["outputs"]) for r in records),"asset_count":sum(r["metadata"]["asset_count"] for r in records),"source_count":sum(r["metadata"]["source_count"] for r in records),"entity_candidate_count":len([c for c in candidates if c.get('status')=='pending']),"coverage_status":"complete"}
    validate(meta,schema_for(vault,"weekly-moc.schema.json"),str(rel))
    rows=[]
    for r in sorted(records,key=lambda x:(x["metadata"]["created_at"],x["metadata"]["chat_id"]),reverse=True):
        m=r["metadata"]; outputs=str(len(r["outputs"])) if r["outputs"] else ""
        rows.append(f"| {m['created_at'][:10]} | {m['updated_at'][:10]} | {markdown_escape(m['title'])} | {markdown_escape(r.get('moc_summary',m['summary']))} | {', '.join(m['contexts'])} | {', '.join(m['content_types'])} | {'; '.join(m['projects'])} | [Open]({m['chat_url']}) | [[{r['chat_rel']}|Note]] |  | {outputs} | {m['workflow_status']} |")
    candidate_rows="\n".join(f"| {markdown_escape(c['proposed_name'])} | {c['proposed_axis']} | {c['evidence_chat_ids']} | {c['confidence']} | Review in [[09 - System/Registries/Entity Candidates]] |" for c in candidates if c.get("status")=="pending") or "_None._"
    body=f"\n# ChatGPT Weekly MOC · {iso_week}\n\n## Chat overview\n\n| Created | Updated | Chat | What was done | Context | Content types | Projects | ChatGPT | Chat note | Human note | Outputs | Status |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n"+"\n".join(rows)+"\n\n## Entity candidates requiring review\n\n| Candidate | Proposed axis | Evidence | Confidence | Action |\n|---|---|---|---|---|\n"+candidate_rows+"\n\n## Run health\n\n- Coverage: complete\n- Validation failures: 0\n"
    atomic_write(vault/rel,dump_frontmatter(meta)+body)
    return vault/rel
