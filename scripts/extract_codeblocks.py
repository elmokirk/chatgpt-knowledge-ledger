"""Exercise code extraction through the canonical renderer; code is never executed."""
from pathlib import Path
import argparse, json
from ledger.ingest import normalize_export
from ledger.render import render_conversation
p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("vault",type=Path); a=p.parse_args(); rows=[render_conversation(c,a.vault) for c in normalize_export(a.input)]; print(json.dumps([o for r in rows for o in r["outputs"]],indent=2,default=str))
