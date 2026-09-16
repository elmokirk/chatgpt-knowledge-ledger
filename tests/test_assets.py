from __future__ import annotations
import json, shutil, tempfile, unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts"))
from asset_reconcile import reconcile

class AssetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(prefix="asset-test-")); self.inbox=self.tmp/"inbox"; self.store=self.tmp/"store"; shutil.copytree(ROOT/"tests"/"fixtures"/"assets"/"inbox",self.inbox); self.store.mkdir()
        self.expected=ROOT/"tests"/"fixtures"/"assets"/"expected.json"
    def tearDown(self): shutil.rmtree(self.tmp)
    def test_report_only_never_moves(self):
        before={p.name:p.read_bytes() for p in self.inbox.iterdir()}; result=reconcile(self.inbox,self.store,self.expected); self.assertEqual(result["operations"],[]); self.assertEqual(before,{p.name:p.read_bytes() for p in self.inbox.iterdir()}); self.assertEqual(list(self.store.iterdir()),[])
    def test_unsafe_is_quarantined(self):
        result=reconcile(self.inbox,self.store,self.expected); danger=next(x for x in result["candidates"] if x["filename"]=="danger.exe"); self.assertEqual(danger["tier"],"D"); self.assertEqual(danger["match_state"],"quarantined")
    def test_explicit_tier_a_move_and_receipt(self):
        plan=reconcile(self.inbox,self.store,self.expected); cid=next(x["candidate_id"] for x in plan["candidates"] if x["filename"]=="demo.png"); result=reconcile(self.inbox,self.store,self.expected,"move_verified",[cid]); self.assertEqual(len(result["operations"]),1); op=result["operations"][0]; self.assertEqual(op["source_cleanup_status"],"verified"); self.assertFalse((self.inbox/"demo.png").exists()); self.assertTrue(Path(op["destination"]).exists())

if __name__=="__main__": unittest.main()
