from __future__ import annotations
import json, shutil, tempfile, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts"))
from chatlog import ingest
from scaffold_demo import scaffold
from ledger.contracts import validate, schema_for, ValidationError
from ledger.entities import update_candidates
from ledger.ingest import inspect_export, normalize_export, ExportError
from ledger.util import parse_frontmatter
from ledger.validate_vault import validate_vault
from sync_recent import evaluate

FIX=ROOT/"tests"/"fixtures"/"exports"/"positive"/"representative-export.json"

def tree_bytes(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(prefix="ledger-test-")); self.vault=self.tmp/"vault"; scaffold(self.vault)
    def tearDown(self): shutil.rmtree(self.tmp)
    def test_inspection_and_unknown_fields(self):
        report=inspect_export(FIX); self.assertEqual(report["conversation_count"],6); self.assertGreaterEqual(report["branch_points"],1); self.assertGreaterEqual(report["unknown_field_count"],1)
    def test_missing_identity_rejected(self):
        with self.assertRaises(ExportError): normalize_export(ROOT/"tests"/"fixtures"/"exports"/"negative"/"missing-id.json")
    def test_ingest_is_deterministic_and_valid(self):
        first=ingest(FIX,self.vault); self.assertTrue(first["validation"]["ok"],first["validation"]["errors"]); before=tree_bytes(self.vault); second=ingest(FIX,self.vault); self.assertTrue(second["validation"]["ok"]); self.assertEqual(before,tree_bytes(self.vault))
    def test_branch_and_large_code_artifact(self):
        result=ingest(FIX,self.vault); self.assertEqual(sum(len(x["branch_rels"]) for x in result["records"]),1); outputs=list((self.vault/"04 - Outputs"/"Records").glob("*.md")); self.assertEqual(len(outputs),1); meta=parse_frontmatter(outputs[0].read_text(encoding="utf-8")); self.assertGreater(meta["line_count"],300); self.assertTrue((self.vault/meta["local_file"].strip("[]")).exists())
    def test_companion_is_never_overwritten(self):
        note=self.vault/"02A - Annotations"/"2026"/"2026-09"/"owner-note.md"; note.parent.mkdir(parents=True); note.write_text("human owned\n",encoding="utf-8"); ingest(FIX,self.vault); before=note.read_bytes(); ingest(FIX,self.vault); self.assertEqual(before,note.read_bytes())
    def test_weekly_moc_exposes_required_axes(self):
        ingest(FIX,self.vault); moc=next(p for p in (self.vault/"01 - MOCs"/"Weekly").rglob("*.md") if p.name != "Index.md"); text=moc.read_text(encoding="utf-8"); self.assertIn("Context | Content types | Projects",text); self.assertIn("project, business",text); self.assertIn("Novel Memory Graph",text)
    def test_live_50_coverage_guard(self):
        entries=json.loads((ROOT/"tests"/"fixtures"/"exports"/"positive"/"live-50.json").read_text(encoding="utf-8"))["entries"]; result=evaluate(entries,{str(entries[0]["id"]):{"source_updated_at":entries[0].get("updated_at")}}); self.assertEqual(result["coverage_status"],"risk"); self.assertEqual(sum(result["counts"].values()),result["chat_count"])
    def test_negative_schema(self):
        schema=schema_for(self.vault,"chat-session.schema.json")
        with self.assertRaises(ValidationError): validate({"schema":"chatgpt-session/v1","note_type":"chat_session","contexts":[],"content_types":["invented"]},schema)
    def test_entity_candidates_deduplicate(self):
        q=self.vault/"09 - System"/"Registries"/"Entity Candidates.yaml"; p=[{"axis":"concept","name":"New Concept","chat_ids":["a"],"confidence":"high"}]; update_candidates(q,p,"2026-09-12T10:00:00+00:00"); rows=update_candidates(q,p,"2026-09-12T10:00:00+00:00"); row=next(x for x in rows if x["proposed_name"]=="New Concept"); self.assertEqual(row["occurrence_count"],"1")
    def test_scaffold_paths_are_portable(self):
        reserved={"CON","PRN","AUX","NUL",*(f"COM{i}" for i in range(1,10)),*(f"LPT{i}" for i in range(1,10))}; paths=[p.relative_to(self.vault) for p in self.vault.rglob("*")]; folded=[p.as_posix().casefold() for p in paths]
        self.assertEqual(len(folded),len(set(folded)))
        for path in paths:
            for part in path.parts:
                self.assertFalse(set('<>:"/\\|?*') & set(part)); self.assertFalse(part.endswith((" ","."))); self.assertNotIn(part.split(".")[0].upper(),reserved)

if __name__=="__main__": unittest.main()
