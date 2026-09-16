from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from .util import atomic_write, slugify

def candidate_id(axis: str, name: str) -> str:
    return "candidate_" + slugify(f"{axis}-{name}", 72)

def load_candidates(path: Path) -> list[dict]:
    text=path.read_text(encoding="utf-8") if path.exists() else ""
    rows=[]; current=None
    for line in text.splitlines():
        if line.startswith("  - candidate_id:"):
            current={"candidate_id": line.split(":",1)[1].strip().strip('"')}; rows.append(current)
        elif current and line.startswith("    ") and ":" in line:
            k,v=line.strip().split(":",1); current[k]=v.strip().strip('"')
    return rows

def update_candidates(path: Path, proposals: list[dict], observed_at: str | None = None) -> list[dict]:
    observed_at=observed_at or datetime.now(timezone.utc).isoformat()
    existing={r["candidate_id"]:r for r in load_candidates(path)}
    for p in proposals:
        cid=candidate_id(p["axis"], p["name"]); row=existing.get(cid)
        chats=",".join(sorted(set(p.get("chat_ids", []))))
        if row:
            old=set(filter(None,row.get("evidence_chat_ids","").split(","))); new=set(filter(None,chats.split(",")))
            combined=old|new; row["last_observed_at"]=observed_at; row["occurrence_count"]=str(len(combined)); row["evidence_chat_ids"]=",".join(sorted(combined))
        else:
            existing[cid]={"candidate_id":cid,"proposed_name":p["name"],"proposed_axis":p["axis"],"aliases":",".join(p.get("aliases",[])),"first_observed_at":observed_at,"last_observed_at":observed_at,"evidence_chat_ids":chats,"occurrence_count":"1","confidence":p.get("confidence","medium"),"reason":p.get("reason","unregistered entity"),"status":"pending"}
    lines=["schema: entity-candidates/v1","review_threshold: 10","candidates:"]
    for row in sorted(existing.values(), key=lambda r:r["candidate_id"]):
        lines.append(f"  - candidate_id: \"{row['candidate_id']}\"")
        for key in ("proposed_name","proposed_axis","aliases","first_observed_at","last_observed_at","evidence_chat_ids","occurrence_count","confidence","reason","status"):
            lines.append(f"    {key}: \"{str(row.get(key,'')).replace(chr(34), chr(39))}\"")
    atomic_write(path, "\n".join(lines)+"\n")
    return list(existing.values())
