"""Minimal test-only YAML subset used to run the bundled skill quick validator offline."""
class YAMLError(ValueError):
    pass

def safe_load(text):
    root = {}
    stack = [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if ":" not in raw:
            raise YAMLError(f"unsupported line: {raw}")
        key, value = raw.strip().split(":", 1)
        while stack[-1][0] >= indent:
            stack.pop()
        target = stack[-1][1]
        value = value.strip()
        if not value:
            target[key] = {}
            stack.append((indent, target[key]))
        elif value.startswith('"') and value.endswith('"'):
            target[key] = value[1:-1]
        else:
            target[key] = value
    return root
