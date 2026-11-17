"""Minimal KiCad s-expression reader and symbol-library helpers (stdlib only)."""
import re
from pathlib import Path

_TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')


def parse(text):
    """Parse an s-expression into nested lists. Strings keep a marker class so they round-trip."""
    pos = 0
    stack = [[]]
    n = len(text)
    while pos < n:
        m = _TOK.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            done = stack.pop()
            stack[-1].append(done)
        elif m.group(3) is not None:
            stack[-1].append(Str(m.group(3)))
        elif m.group(4) is not None:
            stack[-1].append(m.group(4))
    return stack[0][0] if stack[0] else None


class Str(str):
    """A quoted string atom."""


def dump(node, indent=0):
    """Serialise back (tab-indented like KiCad)."""
    if isinstance(node, Str):
        return '"' + node.replace('\\', '\\\\').replace('"', '\\"') + '"' if False else '"' + str(node) + '"'
    if isinstance(node, str):
        return node
    if not node:
        return "()"
    head = node[0]
    # short forms: no nested lists -> one line
    if all(not isinstance(x, list) for x in node):
        return "(" + " ".join(dump(x) for x in node) + ")"
    out = "(" + dump(head)
    inline = []
    i = 1
    while i < len(node) and not isinstance(node[i], list):
        inline.append(dump(node[i]))
        i += 1
    if inline:
        out += " " + " ".join(inline)
    pad = "\t" * (indent + 1)
    for child in node[i:]:
        out += "\n" + pad + (dump(child, indent + 1) if isinstance(child, list) else dump(child))
    out += "\n" + "\t" * indent + ")"
    return out


def find(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def first(node, name):
    r = find(node, name)
    return r[0] if r else None


def load_symbol_lib(path):
    """Return {symbol_name: node} for a .kicad_sym file (top-level symbols only)."""
    tree = parse(Path(path).read_text())
    return {str(c[1]): c for c in tree if isinstance(c, list) and c and c[0] == "symbol"}


def resolve_extends(lib, name):
    """Return a self-contained symbol node (follows `extends`)."""
    node = lib[name]
    ext = first(node, "extends")
    if not ext:
        return node
    base = resolve_extends(lib, str(ext[1]))
    merged = [base[0], Str(name)] + [c for c in base[2:] if not (isinstance(c, list) and c and c[0] == "symbol")]
    # base sub-symbols are named after the base: rename to the derived name
    for c in base[2:]:
        if isinstance(c, list) and c and c[0] == "symbol":
            sub = list(c)
            sub[1] = Str(str(sub[1]).replace(str(base[1]), name, 1))
            merged.append(sub)
    # derived properties override base ones
    props = {str(p[1]): p for p in find(node, "property")}
    out = []
    for c in merged:
        if isinstance(c, list) and c and c[0] == "property" and str(c[1]) in props:
            out.append(props.pop(str(c[1])))
        else:
            out.append(c)
    out.extend(props.values())
    return out


def symbol_pins(node):
    """List of dicts: number, name, type, x, y, angle, unit (0 = all units)."""
    pins = []
    name = str(node[1])
    for sub in find(node, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", str(sub[1]))
        unit = int(m.group(1)) if m else 0
        for p in find(sub, "pin"):
            at = first(p, "at")
            pins.append(dict(
                number=str(first(p, "number")[1]), name=str(first(p, "name")[1]), type=p[1],
                x=float(at[1]), y=float(at[2]), angle=float(at[3]) if len(at) > 3 else 0.0,
                unit=unit, hidden=any(x == "hide" or (isinstance(x, list) and x[:2] == ["hide", "yes"]) for x in p),
                length=float(first(p, "length")[1])))
    return pins


def symbol_units(node):
    units = {int(re.search(r"_(\d+)_(\d+)$", str(s[1])).group(1)) for s in find(node, "symbol")
             if re.search(r"_(\d+)_(\d+)$", str(s[1]))}
    return sorted(u for u in units if u > 0) or [1]
