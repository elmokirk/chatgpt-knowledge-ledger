from __future__ import annotations

import json, zipfile
from pathlib import Path

class ExportError(ValueError): pass

def load_export(path: Path):
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            names=[n for n in z.namelist() if Path(n).name == "conversations.json"]
            if not names: raise ExportError("ZIP contains no conversations.json")
            return json.loads(z.read(sorted(names)[0]))
    return json.loads(path.read_text(encoding="utf-8"))

def inspect_export(path: Path) -> dict:
    data=load_export(path); conversations=data.get("conversations", data) if isinstance(data, dict) else data
    if not isinstance(conversations, list): raise ExportError("expected conversation list")
    branches=attachments=unknown=0
    known={"id","conversation_id","title","create_time","update_time","mapping","current_node","contexts","content_types","session_kind","workflow_status","privacy_class","projects","concepts","collections","areas","people","topics","summary","primary_goal"}
    for c in conversations:
        mapping=c.get("mapping",{}); branches += sum(max(0,len(n.get("children",[]))-1) for n in mapping.values())
        attachments += sum(len((n.get("message") or {}).get("attachments",[])) for n in mapping.values())
        unknown += len(set(c)-known)
    return {"source_file":path.name,"source_bytes":path.stat().st_size,"conversation_count":len(conversations),"branch_points":branches,"attachment_references":attachments,"unknown_field_count":unknown,"predicted_storage_bytes":path.stat().st_size*3}

def _message(node):
    m=node.get("message") or {}; author=(m.get("author") or {}).get("role",m.get("role","unknown")); content=m.get("content",{})
    parts=content.get("parts",[]) if isinstance(content,dict) else [content]
    text="\n".join(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,sort_keys=True) for x in parts)
    return {"id":m.get("id") or node.get("id"),"role":author,"created_at":m.get("create_time"),"text":text,"attachments":m.get("attachments",[])}

def normalize_conversation(raw: dict) -> dict:
    chat_id=raw.get("id") or raw.get("conversation_id")
    if not chat_id: raise ExportError("conversation missing identity")
    mapping=raw.get("mapping")
    if not isinstance(mapping,dict): raise ExportError(f"{chat_id}: missing mapping")
    roots=sorted([k for k,v in mapping.items() if not v.get("parent")])
    if not roots: raise ExportError(f"{chat_id}: no root")
    leaves=sorted([k for k,v in mapping.items() if not v.get("children")])
    selected=raw.get("current_node") if raw.get("current_node") in mapping else (leaves[-1] if leaves else roots[0])
    def path_to(node_id):
        path=[]; seen=set()
        while node_id:
            if node_id in seen: raise ExportError(f"{chat_id}: cycle")
            seen.add(node_id); node=mapping[node_id]
            if node.get("message"): path.append(_message({**node,"id":node_id}))
            node_id=node.get("parent")
        return list(reversed(path))
    main=path_to(selected)
    main_ids={m["id"] for m in main}; alternatives=[]
    for leaf in leaves:
        candidate=path_to(leaf)
        if [m["id"] for m in candidate] == [m["id"] for m in main]: continue
        unique=[m for m in candidate if m["id"] not in main_ids]
        if unique: alternatives.append({"branch_id":leaf,"parent_message_id":next((m["id"] for m in reversed(candidate) if m["id"] in main_ids),None),"messages":candidate})
    return {"chat_id":chat_id,"title":raw.get("title") or "Untitled","created_at":raw.get("create_time"),"updated_at":raw.get("update_time") or raw.get("create_time"),"current_node":selected,"main":main,"branches":alternatives,"metadata":{k:raw.get(k) for k in ("contexts","content_types","session_kind","workflow_status","privacy_class","projects","concepts","collections","areas","people","topics","summary","primary_goal")},"raw":raw}

def normalize_export(path: Path) -> list[dict]:
    data=load_export(path); conversations=data.get("conversations",data) if isinstance(data,dict) else data
    return [normalize_conversation(c) for c in conversations]
