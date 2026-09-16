from pathlib import Path
import subprocess, sys
root=Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable,"-m","unittest","discover","-s",str(root/"tests"),"-p","test_assets.py","-v"],cwd=root))

