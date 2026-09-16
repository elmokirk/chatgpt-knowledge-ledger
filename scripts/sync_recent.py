"""Deterministic live-index filtering and coverage guard; app retrieval is supplied externally."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def evaluate(entries, previous_watermark=None, limit=50):
    chats={str(e["id"]):e for e in entries if e.get("kind")=="chatgpt"}
    ordered=sorted(chats.values(),key=lambda x:str(x.get("updated_at","")),reverse=True)
    risk=len(ordered)>=limit
    if previous_watermark and ordered and str(ordered[-1].get("updated_at",""))>previous_watermark: risk=True
    return {"chat_count":len(ordered),"coverage_status":"risk" if risk else "complete","conversations":ordered,"warning":"historic export or manual recovery may be required" if risk else ""}

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("--previous-watermark"); a=p.parse_args(); data=json.loads(a.input.read_text(encoding="utf-8")); print(json.dumps(evaluate(data["entries"],a.previous_watermark),indent=2))
