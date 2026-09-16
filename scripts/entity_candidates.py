from pathlib import Path
import argparse, json
from ledger.entities import update_candidates
p=argparse.ArgumentParser(); p.add_argument("queue",type=Path); p.add_argument("proposals",type=Path); a=p.parse_args(); print(json.dumps(update_candidates(a.queue,json.loads(a.proposals.read_text(encoding="utf-8"))),indent=2))
