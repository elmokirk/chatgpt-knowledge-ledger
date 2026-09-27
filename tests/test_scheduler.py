from __future__ import annotations

import json, shutil, tempfile, unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts"))
from scaffold_demo import scaffold
from ledger.scheduler import begin, finish, status


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


if __name__=="__main__": unittest.main()
