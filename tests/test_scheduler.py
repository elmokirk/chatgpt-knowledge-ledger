from __future__ import annotations

import json, shutil, tempfile, unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts"))
from scaffold_demo import scaffold
from ledger.scheduler import begin, finish, status
from run_manual_scheduler import run


class SchedulerGateTest(unittest.TestCase):
    def test_fail_closed_lock_and_weekly_noop(self):
        temp=Path(tempfile.mkdtemp(prefix="scheduler-test-")); vault=temp/"vault"
        try:
            scaffold(vault); config=vault/"09 - System"/"State"/"scheduler.config.json"; data=json.loads(config.read_text(encoding="utf-8")); data["enabled"]=True; data["identity_guard"]["expected_account_id"]="acct_fixture"; data["identity_guard"]["required_chatgpt_project_ids"]=["g-p-fixture"]; config.write_text(json.dumps(data),encoding="utf-8")
            now="2026-09-28T12:00:00+02:00"
            self.assertEqual(status(vault,now)["action"],"due")
            self.assertEqual(begin(vault,now,"wrong",["g-p-fixture"])["reason"],"account_mismatch")
            self.assertEqual(begin(vault,now,"acct_fixture",[])["reason"],"workspace_sentinel_missing")
            run=begin(vault,now,"acct_fixture",["g-p-fixture"]); self.assertEqual(run["action"],"run")
            self.assertEqual(begin(vault,now,"acct_fixture",["g-p-fixture"])["reason"],"lock_exists")
            finish(vault,"2026-09-28T12:01:00+02:00",run["run_id"],"completed",{"new":1,"updated":0,"unchanged":0,"failed":0},"complete")
            self.assertEqual(status(vault,now)["action"],"noop")
            before=config.read_bytes(); scaffold(vault); self.assertEqual(config.read_bytes(),before)
        finally: shutil.rmtree(temp)

    def test_live_run_merges_registry_and_versions_raw(self):
        temp=Path(tempfile.mkdtemp(prefix="live-run-test-")); vault=temp/"vault"
        try:
            scaffold(vault); registry=vault/"09 - System"/"Registries"/"Chat Registry.json"; data=json.loads(registry.read_text(encoding="utf-8")); data["records"]["existing"]={"note_path":"keep.md"}; registry.write_text(json.dumps(data),encoding="utf-8")
            snapshot=temp/"snapshot.json"; snapshot.write_text(json.dumps({"run_id":"sync-2026-W40-01","retrieved_at":"2026-09-28T12:00:00+02:00","coverage_status":"partial","reason":"synthetic partial live window","counts":{"new":1,"updated":0,"unchanged":0},"records":[{"chat_id":"fixture-live-1","title":"Synthetic live chat","created_at":"2026-09-28T10:00:00+02:00","updated_at":"2026-09-28T11:00:00+02:00","project_id":None,"messages":[],"session_kind":"unknown","primary_goal":"Synthetic live chat","summary":"Synthetic fixture","workflow_status":"unknown","privacy_class":"private","verification_status":"not_verified","contexts":["unknown"],"content_types":["unknown"],"chat_url":"https://chatgpt.com/c/fixture-live-1","page_has_more":False,"change_type":"new"}]}),encoding="utf-8")
            result=run(snapshot,vault); merged=json.loads(registry.read_text(encoding="utf-8"))["records"]
            self.assertTrue(result["validation"]["ok"]); self.assertIn("existing",merged); self.assertIn("fixture-live-1",merged); self.assertTrue((vault/"03 - Transcripts"/"Raw"/"Live"/"sync-2026-W40-01"/"chat_fixture-live-1.json").is_file())
        finally: shutil.rmtree(temp)


if __name__=="__main__": unittest.main()
