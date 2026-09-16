from __future__ import annotations

import json, os, re, tempfile
from pathlib import Path

def canonical_json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def slugify(text: str, limit: int = 64) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9äöüß]+", "-", text, flags=re.I).strip("-")
    return (text[:limit].rstrip("-") or "untitled")

def atomic_write(path: Path, data: str | bytes) -> bool:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == raw:
        return False
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return True

def immutable_write(path: Path, data: str | bytes) -> bool:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == raw:
            return False
        raise FileExistsError(f"refusing to overwrite different bytes: {path}")
    path.write_bytes(raw)
    return True

def yaml_scalar(value) -> str:
    if value is None: return "null"
    if value is True: return "true"
    if value is False: return "false"
    if isinstance(value, (int, float)): return str(value)
    return json.dumps(str(value), ensure_ascii=False)

def dump_frontmatter(data: dict) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            if value: lines += [f"{key}:", *[f"  - {yaml_scalar(v)}" for v in value]]
            else: lines.append(f"{key}: []")
        else: lines.append(f"{key}: {yaml_scalar(value)}")
    return "\n".join(lines) + "\n---\n"

def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"): raise ValueError("missing YAML frontmatter")
    block = text.split("\n---\n", 1)[0].splitlines()[1:]
    result, active = {}, None
    for line in block:
        if line.startswith("  - ") and active:
            result[active].append(json.loads(line[4:]))
        elif ":" in line:
            key, raw = line.split(":", 1); raw = raw.strip(); active = key
            if raw == "": result[key] = []
            elif raw == "[]": result[key] = []
            elif raw == "null": result[key] = None
            elif raw in ("true", "false"): result[key] = raw == "true"
            else:
                try: result[key] = json.loads(raw)
                except json.JSONDecodeError: result[key] = raw
    return result

def safe_relative(root: Path, candidate: Path) -> Path:
    resolved_root, resolved = root.resolve(), candidate.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError(f"path escapes root: {candidate}")
    return resolved
