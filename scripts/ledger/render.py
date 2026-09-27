from __future__ import annotations

import json, re
from datetime import datetime, timezone
from pathlib import Path
from . import PARSER_VERSION
from .contracts import schema_for, validate
from .summaries import compact, policy
from .util import atomic_write, dump_frontmatter, slugify

LANG_EXT={"python":"py","javascript":"js","typescript":"ts","html":"html","css":"css","json":"json","yaml":"yaml","bash":"sh","shell":"sh","powershell":"ps1","sql":"sql"}
FENCE=re.compile(r"```([^\n`]*)\n(.*?)```",re.S)

def iso(value):
    if isinstance(value,(int,float)):
        return datetime.fromtimestamp(value,tz=timezone.utc).isoformat()
    if isinstance(value,str) and value:
        return value if "T" in value else datetime.fromtimestamp(float(value),tz=timezone.utc).isoformat()
    return "1970-01-01T00:00:00+00:00"

def _code_blocks(text, conv, message, branch, ordinal_base, vault, transcript_link):
    records=[]; changed=False
    def replace(match):
        nonlocal changed
        lang=match.group(1).strip().lower() or "text"; code=match.group(2); raw=code.encode("utf-8"); lines=code.count("\n")+1
        if lines <= 300 and len(raw) <= 32768: return match.group(0)
        changed=True; ordinal=len(records)+ordinal_base; ext=LANG_EXT.get(lang,"txt")
        day=iso(conv["created_at"])[:10]; year,month=day[:4],day[5:7]; msg_short=slugify(message["id"],16)
        filename=f"{day}--{slugify(conv['title'])}--{msg_short}--code-{ordinal:02d}.{ext}"
        rel=f"04 - Outputs/Files/{year}/{month}/Code/{filename}"; out_id=f"output_code_{conv['chat_id']}_{message['id']}_{ordinal:02d}"
        rec_rel=f"04 - Outputs/Records/{slugify(conv['title'])}--{msg_short}--code-{ordinal:02d}.md"
        rec={"schema":"chatgpt-output/v2","note_type":"output_record","output_id":out_id,"title":f"{conv['title']} · message {message['id']} · block {ordinal}","output_type":"code_block","origin_chat_ids":[conv["chat_id"]],"origin_message_id":message["id"],"origin_branch_id":branch,"block_ordinal":ordinal,"contexts":conv["metadata"].get("contexts") or ["unknown"],"content_types":conv["metadata"].get("content_types") or ["implementation"],"projects":conv["metadata"].get("projects") or [],"topics":conv["metadata"].get("topics") or [],"language":lang,"file_extension":ext,"line_count":lines,"byte_count":len(raw),"extraction_rule":"line_threshold" if lines>300 else "byte_threshold","local_file":f"[[{rel}]]","source_transcript":f"[[{transcript_link}]]","source_anchor":f"turn-{ordinal:03d}-code-{ordinal:02d}","verification_status":"not_verified"}
        validate(rec,schema_for(vault,"output-record.schema.json"),out_id)
        atomic_write(vault/rel,code); atomic_write(vault/rec_rel,dump_frontmatter(rec)+f"\n# {rec['title']}\n\n- [[{rel}|Open code]]\n- [[{transcript_link}|Source transcript]]\n")
        records.append({"record":rec,"record_rel":rec_rel,"file_rel":rel})
        return f"> [!code] Externalized code block · {lines} lines · {lang}\n> [[{rec_rel}|Code record]] · [[{rel}|Open code]]\n> Source: message `{message['id']}`, block `{ordinal}`"
    return FENCE.sub(replace,text),records,changed

def render_conversation(conv: dict, vault: Path, indexed_at="2026-09-12T12:00:00+02:00") -> dict:
    day=iso(conv["created_at"])[:10]; year,month=day[:4],day[5:7]; short=conv["chat_id"][:8]
    chat_rel=f"02 - Chats/{year}/{year}-{month}/{day} - {conv['title']} - {short}.md"
    raw_rel=f"03 - Transcripts/Raw/Conversations/chat_{conv['chat_id']}.json"
    transcript_rel=f"03 - Transcripts/Normalized/{year}/chat_{conv['chat_id']}.md"
    atomic_write(vault/raw_rel,json.dumps(conv["raw"],ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    refs=[]; rendered=[]; storage="inline"
    for idx,m in enumerate(conv["main"],1):
        body,new,changed=_code_blocks(m["text"],conv,m,"main",1,vault,transcript_rel); refs.extend(new)
        if changed: storage="mixed"
        rendered.append(f"## Turn {idx:03d} · {m['role'].title()} · {iso(m['created_at'])}\n\n<!-- message_id: {m['id']} -->\n\n{body}\n")
    tm={"schema":"chatgpt-transcript/v2","note_type":"normalized_transcript","chat_id":conv["chat_id"],"branch_id":"main","parent_message_id":None,"message_count":len(conv["main"]),"parser_version":PARSER_VERSION,"code_storage":storage,"externalized_code_refs":[f"[[{r['record_rel']}]]" for r in refs]}
    validate(tm,schema_for(vault,"transcript.schema.json"),transcript_rel)
    atomic_write(vault/transcript_rel,dump_frontmatter(tm)+f"\n# Transcript · {conv['title']}\n\n"+"\n".join(rendered))
    branch_rels=[]
    for b in conv["branches"]:
        brel=f"03 - Transcripts/Normalized/{year}/chat_{conv['chat_id']}--branch-{slugify(b['branch_id'],24)}.md"; branch_rels.append(brel)
        bm={**tm,"branch_id":b["branch_id"],"parent_message_id":b["parent_message_id"],"message_count":len(b["messages"])}
        body=[]
        for idx,m in enumerate(b["messages"],1): body.append(f"## Turn {idx:03d} · {m['role'].title()} · {iso(m['created_at'])}\n\n<!-- message_id: {m['id']} -->\n\n{m['text']}\n")
        atomic_write(vault/brel,dump_frontmatter(bm)+f"\n# Transcript branch · {conv['title']}\n\nParent message: `{b['parent_message_id']}`\n\n"+"\n".join(body))
    md=conv["metadata"]; contexts=md.get("contexts") or ["unknown"]; content_types=md.get("content_types") or ["unknown"]; limits=policy(vault)
    chat_summary=compact(md.get("summary"),fallback=f"Conversation: {conv['title']}",max_chars=limits["chat_max_chars"],max_sentences=limits["chat_max_sentences"])
    moc_summary=compact(md.get("moc_summary") or chat_summary,fallback=conv["title"],max_chars=limits["moc_max_chars"],max_sentences=limits["moc_max_sentences"])
    meta={"schema":"chatgpt-session/v2","note_type":"chat_session","session_kind":md.get("session_kind") or "unknown","note_id":"chat_"+conv["chat_id"],"chat_id":conv["chat_id"],"title":conv["title"],"created_at":iso(conv["created_at"]),"updated_at":iso(conv["updated_at"]),"indexed_at":indexed_at,"source_kind":"chatgpt_export","source_batch_id":"fixture_export","source_record":raw_rel,"parser_version":PARSER_VERSION,"chat_url":f"https://chatgpt.com/c/{conv['chat_id']}","chat_url_status":"unverified","chat_url_checked_at":None,"share_url":"","primary_goal":md.get("primary_goal") or conv["title"],"summary":chat_summary,"workflow_status":md.get("workflow_status") or "unknown","completeness":"full","privacy_class":md.get("privacy_class") or "private","verification_status":"not_verified","areas":md.get("areas") or [],"projects":md.get("projects") or [],"concepts":md.get("concepts") or [],"collections":md.get("collections") or [],"people":md.get("people") or [],"contexts":contexts,"content_types":content_types,"topics":md.get("topics") or [],"output_types":["code_block"] if refs else [],"output_refs":[f"[[{r['record_rel']}]]" for r in refs],"asset_refs":[],"source_refs":[],"weekly_moc":"","raw_transcript":f"[[{raw_rel}]]","normalized_transcript":f"[[{transcript_rel}]]","annotation_ref":"","turn_count":len(conv["main"]),"branch_count":1+len(conv["branches"]),"asset_count":sum(len(m.get("attachments",[])) for m in conv["main"]),"source_count":0,"has_full_transcript":True,"has_branches":bool(conv["branches"]),"has_assets":any(m.get("attachments") for m in conv["main"]),"has_open_loops":False,"has_annotation":False}
    validate(meta,schema_for(vault,"chat-session.schema.json"),chat_rel)
    artifact_rows="\n".join(f"| [[{r['record_rel']}|Code]] | code_block | not_verified | [[{r['file_rel']}|File]] | [[{transcript_rel}#{r['record']['source_anchor']}|Message]] |" for r in refs) or "_None._"
    body=f"\n# {conv['title']}\n\n> [!abstract] Abstract\n> {meta['summary']}\n\n## Navigation\n\n- [[#Intent and success criteria]]\n- [[#Outcomes]]\n- [[#Outputs and assets]]\n- [[#Transcript references]]\n\n## Intent and success criteria\n\n- **Primary goal:** {meta['primary_goal']}\n\n## Starting context and inputs\n\nSee transcript.\n\n## Outcomes\n\n- Fixture-normalized conversation.\n\n## Decisions\n\n_None recorded._\n\n## Iterations and feedback\n\n_None recorded._\n\n## Outputs and assets\n\n| Record | Kind | State | Local file | Origin |\n|---|---|---|---|---|\n{artifact_rows}\n\n## Verification and evidence\n\n- **Verification:** not_verified\n\n## Research and sources\n\n_None recorded._\n\n## Failures and blockers\n\n_None recorded._\n\n## Open loops and next actions\n\n_None._\n\n## Reuse and transferability\n\nUse exact transcript evidence.\n\n## Related knowledge\n\n- **Contexts:** {', '.join(contexts)}\n- **Content types:** {', '.join(content_types)}\n\n## Transcript references\n\n- [Open original ChatGPT conversation]({meta['chat_url']})\n- [[{transcript_rel}|Normalized transcript]]\n- [[{raw_rel}|Raw conversation record]]\n"
    atomic_write(vault/chat_rel,dump_frontmatter(meta)+body)
    return {"chat_rel":chat_rel,"transcript_rel":transcript_rel,"branch_rels":branch_rels,"outputs":refs,"metadata":meta,"moc_summary":moc_summary}
