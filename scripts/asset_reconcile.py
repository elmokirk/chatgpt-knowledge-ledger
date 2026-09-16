from __future__ import annotations

import argparse, filecmp, json, mimetypes, shutil, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ledger.util import atomic_write, safe_relative, slugify

UNSAFE={".exe",".msi",".bat",".cmd",".ps1",".sh",".js",".py",".jar",".zip",".rar",".7z",".docm",".xlsm"}

def inventory(inbox: Path):
    root=inbox.resolve(); rows=[]
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        safe_relative(root,path); ext=path.suffix.lower()
        rows.append({"source":str(path.resolve()),"relative_source":path.relative_to(root).as_posix(),"filename":path.name,"size":path.stat().st_size,"mime":mimetypes.guess_type(path.name)[0] or "application/octet-stream","unsafe":ext in UNSAFE})
    return rows

def reconcile(inbox: Path, asset_root: Path, expected_path: Path | None, mode="report_only", approved_ids=None):
    if mode not in {"report_only","move_verified"}: raise ValueError("unsupported mode")
    rows=inventory(inbox); expected=json.loads(expected_path.read_text(encoding="utf-8")) if expected_path else []
    by_name={}
    for e in expected: by_name.setdefault(e.get("filename"),[]).append(e)
    plan=[]
    for row in rows:
        matches=[]; method="suggested"; tier="D" if row["unsafe"] else "C"
        named=by_name.get(row["filename"],[])
        exact=[]
        for item in named:
            reference=(expected_path.parent/item["reference_file"]).resolve() if expected_path and item.get("reference_file") else None
            if reference and reference.is_file() and filecmp.cmp(row["source"],reference,shallow=False): exact.append(item)
        if len(exact)==1: matches=exact; method="exact_bytes"; tier="A"
        elif len(named)==1: matches=named; method="explicit_filename"; tier="B"
        status="quarantined" if row["unsafe"] else ("verified" if tier=="A" else "ambiguous" if len(matches)>1 else "unmatched")
        plan.append({**row,"candidate_id":"asset_"+slugify(row["relative_source"],72),"tier":tier,"match_method":method,"match_state":status,"expected_ids":[m.get("asset_id") for m in matches]})
    receipt={"schema":"asset-reconciliation/v1","mode":mode,"source_root":str(inbox.resolve()),"destination_root":str(asset_root.resolve()),"operations":[],"candidates":plan}
    if mode=="move_verified":
        approved=set(approved_ids or [])
        for item in plan:
            if item["tier"]!="A" or item["unsafe"] or item["candidate_id"] not in approved: continue
            src=safe_relative(inbox,Path(item["source"])); dest=asset_root/f"{slugify(src.stem)}{src.suffix.lower()}"; safe_relative(asset_root,dest)
            if dest.exists() and not filecmp.cmp(src,dest,shallow=False): raise FileExistsError(f"collision: {dest}")
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists(): shutil.move(str(src),str(dest))
            receipt["operations"].append({"candidate_id":item["candidate_id"],"operation_kind":"move","source":str(src),"destination":str(dest),"source_cleanup_status":"verified" if not src.exists() else "failed","rollback":{"from":str(dest),"to":str(src)}})
    return receipt

def main():
    p=argparse.ArgumentParser(); p.add_argument("mode",choices=["scan","match","plan-moves","move-verified","rollback","validate"]); p.add_argument("--inbox",type=Path); p.add_argument("--asset-root",type=Path); p.add_argument("--expected",type=Path); p.add_argument("--manifest",type=Path); p.add_argument("--approved-id",action="append",default=[])
    a=p.parse_args()
    if a.mode in {"scan","match","plan-moves","validate"}: result=reconcile(a.inbox,a.asset_root,a.expected,"report_only")
    elif a.mode=="move-verified": result=reconcile(a.inbox,a.asset_root,a.expected,"move_verified",a.approved_id)
    else:
        data=json.loads(a.manifest.read_text(encoding="utf-8")); result={"schema":"asset-rollback/v1","operations":[]}
        for op in reversed(data.get("operations",[])):
            src,dst=Path(op["from"]),Path(op["to"]); dst.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(src),str(dst)); result["operations"].append({"from":str(src),"to":str(dst)})
    if a.manifest and a.mode!="rollback": atomic_write(a.manifest,json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
