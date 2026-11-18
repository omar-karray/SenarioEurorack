#!/usr/bin/env python3
"""Write the Senario schematic (root + 5 sheets) from design.py.

Every pin gets a short wire and a global label (or a power symbol), so the schematic is a readable netlist:
the connections are the net names. Run from anywhere:  gen_schematic.py <out dir>
"""
import math
import re
import sys
import uuid
from collections import OrderedDict, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import design as D
from kicad_sexp import (Str, dump, find, first, load_symbol_lib, parse, resolve_extends, symbol_pins,
                        symbol_units)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                       # repo root
SYM_DIRS = [HERE.parent / "lib", ROOT / "KicadLibs" / "symbols",
            Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")]
NS = uuid.UUID("6f0a4a52-1f1c-4c2b-9d0e-5e4a53454e41")
POWER_POS = {"+12V", "+5V", "+3V3", "+3V3A"}
POWER_NEG = {"-12V"}
POWER_NETS = POWER_POS | POWER_NEG | {"GND"}
SHEETS = OrderedDict([("Power", "Power supply: Eurorack input, +5 V, -10 V reference, Seed VIN"),
                      ("Daisy", "Daisy Seed2 DFM"),
                      ("Audio", "Audio: Seed codec in/out, external PCM3060 in/out, jacks"),
                      ("CV_Gate", "CV in/out, gate in/out, MIDI"),
                      ("Controls", "I/O expanders, LED drivers, analog mux, OLED, panel controls")])
_libs = {}


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(map(str, key))))


def lib_symbol(libid):
    lib, name = libid.split(":", 1)
    if lib not in _libs:
        for d in SYM_DIRS:
            f = d / f"{lib}.kicad_sym"
            if f.exists():
                _libs[lib] = load_symbol_lib(f)
                break
        else:
            raise FileNotFoundError(lib)
    node = resolve_extends(_libs[lib], name)
    node = list(node)
    node[1] = Str(libid)
    return node


def prop(node, name):
    for p in find(node, "property"):
        if str(p[1]) == name:
            return str(p[2])
    return ""


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


class Sym:
    """A library symbol with pin geometry."""

    def __init__(self, libid):
        self.id = libid
        self.node = lib_symbol(libid)
        self.pins = symbol_pins(self.node)
        self.units = symbol_units(self.node)
        self.vertical2 = len({p["x"] for p in self.pins}) == 1 and len(self.pins) == 2 and not libid.startswith("power:")

    def pin_by_key(self, key):
        """name first (all matches), then number. Needed for the Seed: pad 'D8' is the pin named 'D32'."""
        res = [p for p in self.pins if p["name"] == key]
        if not res:
            res = [p for p in self.pins if p["number"] == key]
        return res


_syms = {}


def sym(libid):
    if libid not in _syms:
        _syms[libid] = Sym(libid)
    return _syms[libid]


def xform(pin, rot):
    """Pin position and outward direction in sheet-relative coordinates (y down)."""
    r = math.radians(rot)
    x, y = pin["x"], pin["y"]
    xr, yr = x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)
    a = math.radians(pin["angle"] + 180 + rot)
    return (round(xr, 4), round(-yr, 4)), (round(math.cos(a)), round(-math.sin(a)))


def unit_pins(s, unit):
    return [p for p in s.pins if p["unit"] in (0, unit)]


def resolve_pins(part, s):
    """Map symbol pin number -> net (None = no connect) for one part."""
    out = {}
    for key, net in part["pins"].items():
        ps = s.pin_by_key(key)
        if not ps:
            raise KeyError(f"{part['ref']}: no pin '{key}' in {s.id}")
        for p in ps:
            out[p["number"]] = net
    return out


def expand_unused_units(part, s, nets):
    """Unused op-amp units: output tied to the inverting input, + to GND."""
    if not part["sym"].endswith(("TL074", "MCP6004")):
        return
    for u in s.units:
        ps = unit_pins(s, u)
        if u == 5 or any(p["number"] in nets for p in ps):
            continue
        num = {p["number"]: p for p in ps}
        outp = [p for p in ps if p["name"] == "" and p["type"] == "output"] or [p for p in ps if p["type"] == "output"]
        inn = [p for p in ps if p["name"] == "-"]
        inp = [p for p in ps if p["name"] == "+"]
        net = f"UNUSED_{part['ref']}_{u}"
        nets[outp[0]["number"]] = net
        nets[inn[0]["number"]] = net
        nets[inp[0]["number"]] = "GND"


def label_w(net):
    return len(net) * 1.0 + 3.0


class Sheet:
    def __init__(self, name, root_uuid, sheet_uuid):
        self.name = name
        self.root = root_uuid
        self.uuid = sheet_uuid
        self.items = []
        self.used_syms = OrderedDict()
        self.pwr_n = 0

    def add(self, s):
        self.items.append(s)

    def inst(self, ref, unit):
        return (f'(instances (project "Senario" (path "/{self.root}/{self.uuid}" (reference "{ref}") (unit {unit}))))')

    def place(self, part, s, unit, X, Y, rot, nets):
        """Emit the symbol instance, wires, labels, power symbols and no-connects. Returns nothing."""
        ref = part["ref"]
        self.used_syms[s.id] = s
        hide = "(hide yes)"
        fs = "(font (size 1.27 1.27))"
        lines = [f'(symbol (lib_id "{s.id}") (at {fmt(X)} {fmt(Y)} {rot}) (unit {unit})']
        lines.append("\t(exclude_from_sim no) (in_bom %s) (on_board %s) (dnp no)" %
                     ("no" if part["sym"].startswith("power:") else "yes",
                      "no" if part["sym"].startswith("power:") or not part["fp"] else "yes"))
        lines.append(f'\t(uuid "{uid(self.name, ref, unit)}")')
        lines.append(f'\t(property "Reference" "{ref}" (at {fmt(X)} {fmt(Y - 6)} 0) (effects {fs}))')
        lines.append(f'\t(property "Value" "{part["value"]}" (at {fmt(X)} {fmt(Y + 6)} 0) (effects {fs}))')
        lines.append(f'\t(property "Footprint" "{part["fp"] or ""}" (at {fmt(X)} {fmt(Y)} 0) (effects {fs} {hide}))')
        lines.append(f'\t(property "Datasheet" "" (at {fmt(X)} {fmt(Y)} 0) (effects {fs} {hide}))')
        for k, v in part["props"].items():
            lines.append(f'\t(property "{k}" "{v}" (at {fmt(X)} {fmt(Y)} 0) (effects {fs} {hide}))')
        for p in unit_pins(s, unit):
            lines.append(f'\t(pin "{p["number"]}" (uuid "{uid(self.name, ref, unit, p["number"])}"))')
        lines.append("\t" + self.inst(ref, unit) + ")")
        self.add("\n".join(lines))
        # connections
        for p in unit_pins(s, unit):
            (px, py), (dx, dy) = xform(p, rot)
            ax, ay = X + px, Y + py
            net = nets.get(p["number"], "__nc__")
            if net in (None, "__nc__"):
                if p["hidden"] and p["type"] == "no_connect":
                    continue
                self.add(f'(no_connect (at {fmt(ax)} {fmt(ay)}) (uuid "{uid(self.name, ref, unit, p["number"], "nc")}"))')
                continue
            bx, by = ax + dx * 2.54, ay + dy * 2.54
            self.add(f'(wire (pts (xy {fmt(ax)} {fmt(ay)}) (xy {fmt(bx)} {fmt(by)})) (stroke (width 0) (type default)) '
                     f'(uuid "{uid(self.name, ref, unit, p["number"], "w")}"))')
            if net in POWER_NETS:
                self.power(net, bx, by, (ref, unit, p["number"]))
            else:
                ang = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}[(dx, dy)]
                just = "(justify right)" if ang == 180 else "(justify left)"
                self.add(f'(global_label "{net}" (shape bidirectional) (at {fmt(bx)} {fmt(by)} {ang}) '
                         f'(effects (font (size 1 1)) {just}) (uuid "{uid(self.name, ref, unit, p["number"], "l")}") '
                         f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {fmt(bx)} {fmt(by)} 0) '
                         f'(effects (font (size 1.27 1.27)) (hide yes))))')

    def power(self, net, x, y, key):
        libid = "power:GND" if net == "GND" else ("power:-12V" if net in POWER_NEG else "power:+3V3")
        s = sym(libid)
        self.used_syms[libid] = s
        self.pwr_n += 1
        ref = f"#PWR{self.name[:2].upper()}{self.pwr_n:03d}"
        fs = "(font (size 1.27 1.27))"
        self.add(f'(symbol (lib_id "{libid}") (at {fmt(x)} {fmt(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no)\n'
                 f'\t(uuid "{uid(self.name, "pwr", self.pwr_n)}")\n'
                 f'\t(property "Reference" "{ref}" (at {fmt(x)} {fmt(y)} 0) (effects {fs} (hide yes)))\n'
                 f'\t(property "Value" "{net}" (at {fmt(x)} {fmt(y + (3.5 if net == "GND" else -3.5))} 0) (effects {fs}))\n'
                 f'\t(property "Footprint" "" (at {fmt(x)} {fmt(y)} 0) (effects {fs} (hide yes)))\n'
                 f'\t(property "Datasheet" "" (at {fmt(x)} {fmt(y)} 0) (effects {fs} (hide yes)))\n'
                 f'\t(pin "1" (uuid "{uid(self.name, "pwr", self.pwr_n, "p")}"))\n'
                 f'\t(instances (project "Senario" (path "/{self.root}/{self.uuid}" (reference "{ref}") (unit 1)))))')

    def text(self, s, x, y, size=2.5):
        self.add(f'(text "{s}" (exclude_from_sim no) (at {fmt(x)} {fmt(y)} 0) (effects (font (size {size} {size}) (bold yes)) '
                 f'(justify left bottom)) (uuid "{uid(self.name, "t", s, x, y)}"))')

    def render(self, paper, title):
        libs = "\n".join("\t" + dump(s.node, 1) for s in self.used_syms.values())
        body = "\n".join(self.items)
        return (f'(kicad_sch\n\t(version 20250114)\n\t(generator "senario_gen")\n\t(generator_version "1.0")\n'
                f'\t(uuid "{self.uuid}")\n\t(paper "{paper}")\n'
                f'\t(title_block (title "{title}") (date "2026-11-18") (rev "A0") (company "Senario") '
                f'(comment 1 "Generated by SenarioHW/Kicad/scripts/gen_schematic.py from design.py"))\n'
                f'\t(lib_symbols\n{libs}\n\t)\n{body}\n'
                f'\t(embedded_fonts no)\n)\n')


PAPERS = [("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594), ("A0", 1189, 841)]


def build(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    root_uuid = uid("root")
    # power flags on rails that only connect to power-input pins
    with D.blk("Power", "power"):
        for net in ("GND", "+12V", "-12V", "+3V3", "+3V3A", "DSY_VIN"):
            D.part("FLG", "power:PWR_FLAG", "", "PWR_FLAG", {"1": net}, ref_="#FLG%02d" % (len(D.PARTS) % 100))
    bysheet = defaultdict(list)
    for p in D.PARTS:
        bysheet[p["sheet"]].append(p)
    sheets = {}
    for name in SHEETS:
        sh = Sheet(name, root_uuid, uid("sheet", name))
        parts = bysheet[name]
        # group by block, keep definition order
        blocks = OrderedDict()
        for p in parts:
            blocks.setdefault(p["block"], []).append(p)
        W = 400.0
        x = y = 15.0
        row_h = 0.0
        ymax = 0.0
        for bname, plist in blocks.items():
            if x > 15.0:
                x, y = 15.0, y + row_h + 8
                row_h = 0.0
            sh.text(f"{bname}", x, y)
            y += 6
            x0, rowtop = 15.0, y
            x, row_h = 15.0, 0.0
            for p in plist:
                s = sym(p["sym"])
                nets = resolve_pins(p, s)
                expand_unused_units(p, s, nets)
                rot = 90 if s.vertical2 else 0
                for u in s.units:
                    ups = unit_pins(s, u)
                    if u not in (0,) and not any(q["number"] in nets for q in ups) and len(s.units) > 1 and u != 1:
                        continue
                    pts = [xform(q, rot) for q in ups] or [((0.0, 0.0), (0, 0))]
                    minx = min(a[0][0] for a in pts); maxx = max(a[0][0] for a in pts)
                    miny = min(a[0][1] for a in pts); maxy = max(a[0][1] for a in pts)
                    lw = max([label_w(nets.get(q["number"]) or "x") for q in ups] + [8])
                    left = 2.54 + (lw if any(d[0] == -1 for _, d in pts) else 0)
                    right = 2.54 + (lw if any(d[0] == 1 for _, d in pts) else 0)
                    cw = (maxx - minx) + left + right + 6
                    chh = (maxy - miny) + 22
                    if x + cw > W and x > 15.0:
                        x, y = 15.0, y + row_h + 4
                        row_h = 0.0
                    X = round((x + left - minx) / 2.54) * 2.54
                    Y = round((y + 8 - miny) / 2.54) * 2.54
                    sh.place(p, s, u, X, Y, rot, nets)
                    x += cw
                    row_h = max(row_h, chh)
            ymax = max(ymax, y + row_h)
            x = 15.0
            y = y + row_h
            row_h = 0.0
            x = 15.0
        height = ymax + 20
        paper = next(pp for pp in PAPERS if pp[1] >= W + 20 and pp[2] >= height) if height < 841 else PAPERS[-1]
        # if height too big for A3 use bigger paper and re-wide? keep width fixed (fine)
        sheets[name] = sh.render(paper[0], SHEETS[name])
        (out / f"{name}.kicad_sch").write_text(sheets[name])
    # root
    items = []
    n = 0
    for name in SHEETS:
        n += 1
        x = 30 + ((n - 1) % 3) * 90
        y = 40 + ((n - 1) // 3) * 40
        su = uid("sheet", name)
        items.append(
            f'(sheet (at {x} {y}) (size 70 20) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)\n'
            f'\t(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0))\n\t(uuid "{su}")\n'
            f'\t(property "Sheetname" "{name}" (at {x} {y - 0.7} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))\n'
            f'\t(property "Sheetfile" "{name}.kicad_sch" (at {x} {y + 20.7} 0) (effects (font (size 1.27 1.27)) (justify left top)))\n'
            f'\t(instances (project "Senario" (path "/{root_uuid}" (page "{n + 1}")))))')
        items.append(f'(text "{SHEETS[name]}" (exclude_from_sim no) (at {x} {y + 26} 0) (effects (font (size 1.5 1.5)) (justify left)) '
                     f'(uuid "{uid("rt", name)}"))')
    root = (f'(kicad_sch\n\t(version 20250114)\n\t(generator "senario_gen")\n\t(generator_version "1.0")\n\t(uuid "{root_uuid}")\n'
            f'\t(paper "A4")\n\t(title_block (title "Senario Looper / MultiFX") (date "2026-11-18") (rev "A0") (company "Senario") '
            f'(comment 1 "22HP Eurorack, Daisy Seed2 DFM") (comment 2 "Generated: SenarioHW/Kicad/scripts"))\n'
            f'\t(lib_symbols)\n' + "\n".join(items) +
            f'\n\t(sheet_instances (path "/" (page "1")))\n\t(embedded_fonts no)\n)\n')
    (out / "Senario.kicad_sch").write_text(root)
    return out


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else HERE.parent)
    print("schematic written,", len(D.PARTS), "parts")
