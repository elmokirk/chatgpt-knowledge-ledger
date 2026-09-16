from __future__ import annotations

import argparse, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ledger.ingest import inspect_export, normalize_export
from ledger.render import render_conversation
from ledger.indexes import render_weekly
from ledger.entities import update_candidates
from ledger.validate_vault import validate_vault
from ledger.util import atomic_write

ROOT=Path(__file__).resolve().parents[1]

def ingest(input_path: Path, vault: Path):
    normalized=normalize_export(input_path)
    records=[render_conversation(c,vault) for c in normalized]
    proposals=[]
    for conv in normalized:
        for proposal in conv["raw"].get("entity_candidates", []):
            proposals.append({**proposal,"chat_ids":[conv["chat_id"]]})
    candidates=update_candidates(vault/"09 - System"/"Registries"/"Entity Candidates.yaml",proposals,"2026-09-12T12:00:00+02:00") if proposals else []
    moc=render_weekly(vault,records,candidates=candidates)
    report=validate_vault(vault)
    run={"schema":"chatgpt-ingest-run/v2","note_type":"ingest_run","run_id":"run_ingest_"+input_path.stem,"mode":"ingest_export","started_at":"2026-09-12T12:00:00+02:00","completed_at":"2026-09-12T12:00:00+02:00","status":"completed" if report["ok"] else "failed","parser_version":"2.0.0","schema_version":"v2","source_file":input_path.name,"source_bytes":input_path.stat().st_size,"counts":{"chats":len(records)},"warnings":[],"errors":report["errors"]}
    run_path=vault/"09 - System"/"Runs"/"2026"/f"2026-09-12T12-00-00 - Run Report.json"; atomic_write(run_path,json.dumps(run,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    return {"records":records,"weekly_moc":str(moc),"validation":report,"run_report":str(run_path)}

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    q=sub.add_parser("init"); q.add_argument("--vault",required=True,type=Path)
    q=sub.add_parser("inspect-export"); q.add_argument("--input",required=True,type=Path)
    q=sub.add_parser("ingest-export"); q.add_argument("--input",required=True,type=Path); q.add_argument("--vault",required=True,type=Path)
    q=sub.add_parser("validate"); q.add_argument("--vault",required=True,type=Path)
    q=sub.add_parser("rebuild-indexes"); q.add_argument("--vault",required=True,type=Path)
    a=p.parse_args()
    if a.cmd=="init":
        from scaffold_demo import scaffold
        scaffold(a.vault); result={"ok":True,"vault":str(a.vault.resolve())}
    elif a.cmd=="inspect-export": result=inspect_export(a.input)
    elif a.cmd=="ingest-export": result=ingest(a.input,a.vault)
    elif a.cmd=="validate": result=validate_vault(a.vault)
    else: result={"ok":True,"message":"Indexes are generated during deterministic ingest; no canonical records changed."}
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str)); raise SystemExit(0 if result.get("ok",result.get("validation",{}).get("ok",True)) else 1)

if __name__=="__main__": main()
