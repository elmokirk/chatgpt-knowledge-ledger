"""Run the weekly live-index pipeline manually without creating an automation."""
from __future__ import annotations

import argparse, hashlib, json, re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ledger import PARSER_VERSION
from ledger.contracts import schema_for, validate
from ledger.entities import update_candidates
from ledger.util import atomic_write, canonical_json, dump_frontmatter, immutable_write
from ledger.validate_vault import validate_vault

# The test run is fixed to September (CEST). The scheduler configuration retains
# the authoritative IANA zone; this local Python build has no bundled tzdata.
BERLIN = timezone(timedelta(hours=2))

def timestamp(value) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, BERLIN).isoformat()
    if isinstance(value, str) and value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(BERLIN).isoformat()
    return "1970-01-01T00:00:00+00:00"

def safe_title(value: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', " - ", value).strip().rstrip(".")[:100] or "Untitled"

def topics_for(title: str) -> list[str]:
    terms = {"webgl":"webgl", "webgpu":"webgpu", "shader":"shader", "nuxt":"nuxt", "tailwind":"tailwind", "n8n":"n8n", "ollama":"ollama", "hermes":"hermes", "golf":"golf", "sales":"sales", "pitch":"sales-pitch", "website":"website", "branding":"branding", "wissensmanagement":"knowledge-management", "trading":"trading", "wav":"audio"}
    low=title.lower(); return sorted({slug for needle,slug in terms.items() if needle in low})

def output_types_for(title: str) -> list[str]:
    low=title.lower(); result=[]
    if any(x in low for x in ("html","demo","webgl","webgpu","shader","website")): result.append("standalone-html")
    if "skill" in low: result.append("skill")
    if any(x in low for x in ("guide","plan","konzept","vergleich","zusammenfassen")): result.append("report")
    if any(x in low for x in ("pitch","sales","outreach")): result.append("sales-document")
    if any(x in low for x in ("wav","transkrib")): result.append("transcript")
    return result

def run(snapshot_path: Path, vault: Path) -> dict:
    source=json.loads(snapshot_path.read_text(encoding="utf-8")); run_id=source["run_id"]; generated_at=source["retrieved_at"]
    year,week,_=datetime.fromisoformat(generated_at).date().isocalendar(); iso_week=f"{year}-W{week:02d}"
    weekly_rel=f"01 - MOCs/Weekly/{year}/{iso_week} - ChatGPT Weekly MOC.md"
    rendered=[]; candidates=[]; registry_path=vault/"09 - System"/"Registries"/"Chat Registry.json"; registry=json.loads(registry_path.read_text(encoding="utf-8"))
    for rec in source["records"]:
        created=timestamp(rec["created_at"]); updated=timestamp(rec["updated_at"]); day=created[:10]; y,m=day[:4],day[5:7]; title=safe_title(rec["title"]); short=rec["chat_id"][:8]
        raw_rel=f"03 - Transcripts/Raw/Live/{run_id}/chat_{rec['chat_id']}.json"
        transcript_rel=f"03 - Transcripts/Normalized/{y}/chat_{rec['chat_id']}.md"
        chat_rel=f"02 - Chats/{y}/{y}-{m}/{day} - {title} - {short}.md"
        immutable_write(vault/raw_rel,json.dumps(rec,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
        messages=rec.get("messages",[])
        transcript_meta={"schema":"chatgpt-transcript/v2","note_type":"normalized_transcript","chat_id":rec["chat_id"],"branch_id":"live-recent","parent_message_id":None,"message_count":len(messages),"parser_version":PARSER_VERSION,"code_storage":"inline","externalized_code_refs":[]}
        validate(transcript_meta,schema_for(vault,"transcript.schema.json"),transcript_rel)
        turns=[]
        for i,msg in enumerate(reversed(messages),1):
            turns.append(f"## Retrieved turn {i:03d} · {msg['role'].title()}\n\n<!-- message_id: {msg['id']} -->\n\n{msg['text']}\n")
        transcript_body=f"\n# Partial live transcript · {rec['title']}\n\n> [!warning] Live delta snapshot\n> This contains only the retrieved recent app window. It is not the historic completeness source.\n\n"+"\n".join(turns)
        atomic_write(vault/transcript_rel,dump_frontmatter(transcript_meta)+transcript_body)
        projects=[]
        if rec.get("project_id"):
            candidates.append({"axis":"project","name":f"ChatGPT Project {rec['project_id']}","chat_ids":[rec["chat_id"]],"confidence":"high","reason":"stable project_id observed in live app metadata"})
        output_types=output_types_for(rec["title"])
        meta={"schema":"chatgpt-session/v2","note_type":"chat_session","session_kind":rec["session_kind"],"note_id":"chat_"+rec["chat_id"],"chat_id":rec["chat_id"],"title":rec["title"],"created_at":created,"updated_at":updated,"indexed_at":generated_at,"source_kind":"chatgpt_live_index","source_batch_id":run_id,"source_record":raw_rel,"parser_version":PARSER_VERSION,"chat_url":rec["chat_url"],"chat_url_status":"unverified","chat_url_checked_at":None,"share_url":"","primary_goal":rec["primary_goal"],"summary":rec["summary"],"workflow_status":rec["workflow_status"],"completeness":"partial","privacy_class":rec["privacy_class"],"verification_status":rec["verification_status"],"areas":[],"projects":projects,"concepts":[],"collections":[],"people":[],"contexts":rec["contexts"],"content_types":rec["content_types"],"topics":topics_for(rec["title"]),"output_types":output_types,"output_refs":[],"asset_refs":[],"source_refs":[],"weekly_moc":f"[[{weekly_rel}]]","raw_transcript":f"[[{raw_rel}]]","normalized_transcript":f"[[{transcript_rel}]]","annotation_ref":"","turn_count":len(messages),"branch_count":1,"asset_count":0,"source_count":0,"has_full_transcript":False,"has_branches":False,"has_assets":False,"has_open_loops":False,"has_annotation":False}
        validate(meta,schema_for(vault,"chat-session.schema.json"),chat_rel)
        body=f"\n# {rec['title']}\n\n> [!abstract] Abstract\n> {rec['summary']}\n\n## Navigation\n\n- [[#Intent and success criteria]]\n- [[#Outcomes]]\n- [[#Related knowledge]]\n- [[#Transcript references]]\n\n## Intent and success criteria\n\n- **Primary goal:** {rec['primary_goal']}\n\n## Starting context and inputs\n\nLive app snapshot; historic source pending export.\n\n## Outcomes\n\n- Recent app content indexed for review.\n\n## Decisions\n\n_Not asserted from the partial live window._\n\n## Iterations and feedback\n\nSee partial transcript.\n\n## Outputs and assets\n\n- **Indicated output types:** {', '.join(output_types) if output_types else 'none identified'}\n\n## Verification and evidence\n\n- **Verification:** not_verified\n- **Completeness:** partial\n\n## Research and sources\n\n_Not normalized during this first live test._\n\n## Failures and blockers\n\n- Historic completeness requires a ChatGPT data export.\n\n## Open loops and next actions\n\n- [ ] Reconcile with historic export.\n\n## Reuse and transferability\n\nReview exact recent turns before reuse.\n\n## Related knowledge\n\n- **Contexts:** {', '.join(meta['contexts'])}\n- **Content types:** {', '.join(meta['content_types'])}\n- **Topics:** {', '.join(meta['topics'])}\n\n## Transcript references\n\n- [Open original ChatGPT conversation]({meta['chat_url']})\n- [[{transcript_rel}|Partial normalized transcript]]\n- [[{raw_rel}|Raw live snapshot]]\n"
        atomic_write(vault/chat_rel,dump_frontmatter(meta)+body)
        rendered.append({"meta":meta,"chat_rel":chat_rel,"change_type":rec.get("change_type","new")})
        registry["records"][rec["chat_id"]]={"note_path":chat_rel,"source_kind":"chatgpt_live_index","last_indexed_at":generated_at,"source_updated_at":rec["updated_at"],"content_digest":hashlib.sha256(canonical_json(rec)).hexdigest()}
    queue=update_candidates(vault/"09 - System"/"Registries"/"Entity Candidates.yaml",candidates,generated_at)
    pending=[x for x in queue if x.get("status")=="pending"]
    start=datetime.fromisoformat(generated_at).date(); start=start.fromordinal(start.toordinal()-start.weekday()); end=start.fromordinal(start.toordinal()+6)
    new_count=sum(x["change_type"]=="new" for x in rendered); updated_count=sum(x["change_type"]=="updated" for x in rendered)
    moc_meta={"schema":"chatgpt-weekly-moc/v1","note_type":"weekly_moc","iso_week":iso_week,"period_start":start.isoformat(),"period_end":end.isoformat(),"generated_at":generated_at,"run_id":run_id,"chat_count":len(rendered),"new_count":new_count,"updated_count":updated_count,"output_count":0,"asset_count":0,"source_count":0,"entity_candidate_count":len(pending),"coverage_status":source["coverage_status"]}
    validate(moc_meta,schema_for(vault,"weekly-moc.schema.json"),weekly_rel)
    rows=[]
    for item in sorted(rendered,key=lambda x:(x["meta"]["updated_at"],x["meta"]["chat_id"]),reverse=True):
        m=item["meta"]; clean=lambda s:str(s).replace("|","\\|").replace("\n"," ")
        rows.append(f"| {m['created_at'][:10]} | {clean(m['title'])} | {clean(m['summary'])} | {', '.join(m['contexts'])} | {', '.join(m['content_types'])} |  | [Open]({m['chat_url']}) | [[{item['chat_rel']}|Note]] |  | {', '.join(m['output_types'])} | {m['workflow_status']} |")
    candidate_rows="\n".join(f"| {x['proposed_name']} | {x['proposed_axis']} | {x['evidence_chat_ids']} | {x['confidence']} | pending |" for x in pending) or "| _None_ | | | | |"
    moc=f"\n# ChatGPT Weekly MOC · {iso_week}\n\n> [!warning] Live coverage\n> {source['reason']}\n\n## Chat overview\n\n| Created | Chat | What was done | Context | Content types | Projects | ChatGPT | Chat note | Human note | Outputs | Status |\n|---|---|---|---|---|---|---|---|---|---|---|\n"+"\n".join(rows)+f"\n\n## Entity candidates requiring review\n\n| Candidate | Proposed axis | Evidence | Confidence | Status |\n|---|---|---|---|---|\n{candidate_rows}\n\n## Run health\n\n- Coverage: {source['coverage_status']}\n- New chats: {new_count}\n- Updated chats: {updated_count}\n- Unchanged chats: {source.get('counts',{}).get('unchanged',0)}\n- Chats with older pages: {sum(1 for x in source['records'] if x['page_has_more'])}\n- Validation is rerun after rendering.\n"
    atomic_write(vault/weekly_rel,dump_frontmatter(moc_meta)+moc)
    atomic_write(registry_path,json.dumps(registry,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    validation=validate_vault(vault)
    state_path=vault/"09 - System"/"State"/"Scheduler State.json"; state=json.loads(state_path.read_text(encoding="utf-8")); state.update({"last_run":run_id,"last_run_at":generated_at,"last_run_coverage":source["coverage_status"],"observed_successful_runs":int(state.get("observed_successful_runs",0))+int(validation["ok"])}); atomic_write(state_path,json.dumps(state,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    return {"run_id":run_id,"counts":{"new":new_count,"updated":updated_count,"unchanged":source.get("counts",{}).get("unchanged",0),"failed":0},"coverage_status":source["coverage_status"],"paged_chats":sum(1 for x in source["records"] if x["page_has_more"]),"weekly_moc":str(vault/weekly_rel),"validation":validation}

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("snapshot",type=Path); parser.add_argument("vault",type=Path); args=parser.parse_args(); result=run(args.snapshot,args.vault); print(json.dumps(result,ensure_ascii=False,indent=2)); raise SystemExit(0 if result["validation"]["ok"] else 1)
