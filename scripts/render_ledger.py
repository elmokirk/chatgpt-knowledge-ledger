from pathlib import Path
import argparse, json
from ledger.ingest import normalize_export
from ledger.render import render_conversation
p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("vault",type=Path); a=p.parse_args(); print(json.dumps([render_conversation(c,a.vault) for c in normalize_export(a.input)],indent=2,default=str))
