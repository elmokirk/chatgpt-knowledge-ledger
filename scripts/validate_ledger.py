from pathlib import Path
import argparse, json
from ledger.validate_vault import validate_vault
p=argparse.ArgumentParser(); p.add_argument("vault",type=Path); a=p.parse_args(); result=validate_vault(a.vault); print(json.dumps(result,indent=2)); raise SystemExit(0 if result["ok"] else 1)
