from __future__ import annotations

import json, re
from datetime import datetime
from pathlib import Path

class ValidationError(ValueError): pass

def _type_ok(value, expected) -> bool:
    names = expected if isinstance(expected, list) else [expected]
    checks = {"string": lambda x: isinstance(x, str), "integer": lambda x: isinstance(x, int) and not isinstance(x, bool), "boolean": lambda x: isinstance(x, bool), "array": lambda x: isinstance(x, list), "object": lambda x: isinstance(x, dict), "null": lambda x: x is None}
    return any(checks[name](value) for name in names)

def validate(instance: dict, schema: dict, where: str = "record") -> None:
    errors=[]
    for key in schema.get("required", []):
        if key not in instance: errors.append(f"{key}: required")
    if schema.get("additionalProperties") is False:
        for key in instance:
            if key not in schema["properties"]: errors.append(f"{key}: unknown property")
    for key, value in instance.items():
        rule=schema.get("properties", {}).get(key)
        if not rule: continue
        if "type" in rule and not _type_ok(value, rule["type"]): errors.append(f"{key}: wrong type")
        if "const" in rule and value != rule["const"]: errors.append(f"{key}: must equal {rule['const']}")
        if "enum" in rule and value not in rule["enum"]: errors.append(f"{key}: value not controlled")
        if isinstance(value, str) and "pattern" in rule and not re.search(rule["pattern"], value): errors.append(f"{key}: pattern mismatch")
        if rule.get("format") == "date-time" and isinstance(value, str):
            try: datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError: errors.append(f"{key}: invalid RFC3339 timestamp")
        if isinstance(value, list):
            if len(value) < rule.get("minItems", 0): errors.append(f"{key}: too few items")
            if rule.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value): errors.append(f"{key}: duplicate items")
            item_rule=rule.get("items", {})
            for item in value:
                if "type" in item_rule and not _type_ok(item, item_rule["type"]): errors.append(f"{key}: invalid item type")
                if "enum" in item_rule and item not in item_rule["enum"]: errors.append(f"{key}: uncontrolled item {item}")
    if errors: raise ValidationError(where + ": " + "; ".join(errors))

def schema_for(vault: Path, name: str) -> dict:
    return json.loads((vault / "09 - System" / "Contracts" / name).read_text(encoding="utf-8"))

