from pathlib import Path
import argparse, json
from chatlog import ingest
p=argparse.ArgumentParser(); p.add_argument("input",type=Path); p.add_argument("vault",type=Path); a=p.parse_args(); print(json.dumps(ingest(a.input,a.vault),indent=2,default=str))
