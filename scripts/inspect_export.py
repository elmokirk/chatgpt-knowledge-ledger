from pathlib import Path
import argparse, json
from ledger.ingest import inspect_export
p=argparse.ArgumentParser(); p.add_argument("input",type=Path); a=p.parse_args(); print(json.dumps(inspect_export(a.input),indent=2))
