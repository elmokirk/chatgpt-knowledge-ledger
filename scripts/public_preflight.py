from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__"}
TEXT_EXT = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".base", ".toml"}
FORBIDDEN_PATHS = {"work", "personal", "backups", "change-proposals"}
PATTERNS = {
    "local user path": re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.I),
    "ChatGPT conversation URL": re.compile(r"chatgpt\.com/c/[0-9a-f-]{16,}", re.I),
    "ChatGPT project identifier": re.compile(r"\bg-p-[0-9a-f]{12,}\b", re.I),
}

def main() -> int:
    errors = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP for part in rel.parts):
            continue
        if rel.parts and rel.parts[0] in FORBIDDEN_PATHS:
            errors.append(f"forbidden path: {rel}")
        if not path.is_file() or path.suffix.lower() not in TEXT_EXT:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label}: {rel}")
    if errors:
        print("Public preflight failed:\n" + "\n".join(f"- {e}" for e in errors))
        return 1
    print("Public preflight passed.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
