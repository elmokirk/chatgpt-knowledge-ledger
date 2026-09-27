"""Deterministic live-index filtering and coverage guard; app retrieval is supplied externally."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def evaluate(entries, previous=None, limit=50):
    previous=previous or {}
    chats={str(e["id"]):{**e,"updated_at":e.get("updated_at",e.get("updatedAt"))} for e in entries if e.get("kind")=="chatgpt"}
    ordered=sorted(chats.values(),key=lambda x:str(x.get("updated_at","")),reverse=True)
    for chat in ordered:
        prior=previous.get(str(chat["id"]))
        chat["change_type"]="new" if not prior else "unchanged" if str(prior.get("source_updated_at"))==str(chat.get("updated_at")) else "updated"
    counts={kind:sum(c["change_type"]==kind for c in ordered) for kind in ("new","updated","unchanged")}
    risk=len(entries)>=limit
    return {"chat_count":len(ordered),"coverage_status":"risk" if risk else "complete","counts":counts,"conversations":ordered,"pending":[c for c in ordered if c["change_type"]!="unchanged"],"warning":"source window reached its limit; historic export or manual recovery may be required" if risk else ""}

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("--registry",type=Path); a=p.parse_args(); data=json.loads(a.input.read_text(encoding="utf-8")); previous=json.loads(a.registry.read_text(encoding="utf-8")).get("records",{}) if a.registry else {}; print(json.dumps(evaluate(data["entries"],previous),indent=2))
