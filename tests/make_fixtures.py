from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def conv(cid,title,kind,contexts,types,user,assistant,branch=False,attachment=False,extra=None):
    nodes={"root":{"id":"root","parent":None,"children":[f"{cid}-u"],"message":None},f"{cid}-u":{"id":f"{cid}-u","parent":"root","children":[f"{cid}-a"],"message":{"id":f"{cid}-u","author":{"role":"user"},"create_time":"2026-09-08T10:00:00+02:00","content":{"parts":[user]},"attachments":[{"name":"demo.png"}]} if attachment else {"id":f"{cid}-u","author":{"role":"user"},"create_time":"2026-09-08T10:00:00+02:00","content":{"parts":[user]}}},f"{cid}-a":{"id":f"{cid}-a","parent":f"{cid}-u","children":[],"message":{"id":f"{cid}-a","author":{"role":"assistant"},"create_time":"2026-09-08T10:01:00+02:00","content":{"parts":[assistant]}}}}
    current=f"{cid}-a"
    if branch:
        nodes[f"{cid}-u"]["children"].append(f"{cid}-alt"); nodes[f"{cid}-alt"]={"id":f"{cid}-alt","parent":f"{cid}-u","children":[],"message":{"id":f"{cid}-alt","author":{"role":"assistant"},"create_time":"2026-09-08T10:02:00+02:00","content":{"parts":["Alternative branch response"]}}}
    row={"id":cid,"title":title,"create_time":"2026-09-08T10:00:00+02:00","update_time":"2026-09-08T10:02:00+02:00","mapping":nodes,"current_node":current,"session_kind":kind,"contexts":contexts,"content_types":types,"workflow_status":"completed","privacy_class":"sensitive" if kind in {"personal","administrative"} else "private","summary":f"Representative {kind} conversation.","primary_goal":user[:100],"projects":[],"concepts":[],"collections":[],"areas":[],"people":[],"topics":[]}
    if extra: row.update(extra)
    return row

large="```typescript\n"+"\n".join(f"export const line{i} = {i};" for i in range(301))+"\n```"
rows=[
 conv("11111111-1111-4111-8111-111111111111","Codrops WebGL Build","build",["project","business"],["implementation","debugging"],"Build a WebGL component",large,attachment=True),
 conv("22222222-2222-4222-8222-222222222222","Website Redesign","build",["project"],["planning","implementation"],"Iterate on a website", "Iteration complete",branch=True),
 conv("33333333-3333-4333-8333-333333333333","CMS Research","research",["business","learning"],["research","review"],"Compare CMS tools","Sources: https://example.com and https://example.org"),
 conv("44444444-4444-4444-8444-444444444444","Sales Pitch","strategy_sales",["business"],["strategy","writing"],"Create a pitch","Pitch and objections drafted"),
 conv("55555555-5555-4555-8555-555555555555","Skill System Design","system_skill",["project"],["planning","implementation"],"Design a skill system","Contracts prepared",extra={"future_unknown":{"kept":True},"entity_candidates":[{"axis":"concept","name":"Novel Memory Graph","confidence":"high","reason":"fixture unknown entity"}]}),
 conv("66666666-6666-4666-8666-666666666666","Website Redesign","personal",["personal"],["review","reflection"],"Reflect on focus","Reflection recorded"),
]
out=ROOT/"fixtures"/"exports"/"positive"/"representative-export.json"; out.write_text(json.dumps({"conversations":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(ROOT/"fixtures"/"exports"/"negative"/"missing-id.json").write_text(json.dumps({"conversations":[{"title":"Broken","mapping":{}}]},indent=2)+"\n",encoding="utf-8")
(ROOT/"fixtures"/"exports"/"positive"/"live-50.json").write_text(json.dumps({"entries":[{"id":f"live-{i:02d}","kind":"chatgpt"} for i in range(50)]},indent=2)+"\n",encoding="utf-8")
inbox=ROOT/"fixtures"/"assets"/"inbox"; inbox.mkdir(parents=True,exist_ok=True); payload=b"fixture-image-payload"; (inbox/"demo.png").write_bytes(payload); (inbox/"danger.exe").write_bytes(b"MZ fixture never execute")
expected=[{"asset_id":"asset_demo","filename":"demo.png","reference_file":"inbox/demo.png"}]; (ROOT/"fixtures"/"assets"/"expected.json").write_text(json.dumps(expected,indent=2)+"\n",encoding="utf-8")
