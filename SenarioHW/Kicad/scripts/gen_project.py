#!/usr/bin/env python3
"""Write Senario.kicad_pro and the project-local symbol / footprint library tables."""
import json, re, sys
from pathlib import Path

out = Path(sys.argv[1])
root = out.parents[1]
stock_s = "${KICAD10_SYMBOL_DIR}"
stock_f = "${KICAD10_FOOTPRINT_DIR}"
rel = "${KIPRJMOD}/../../KicadLibs"
sym_libs = {}
fp_libs = {}
sys.path.insert(0, str(Path(__file__).parent))
import design as D
for p in D.PARTS:
    for libid, d in ((p["sym"], sym_libs), (p["fp"], fp_libs)):
        if libid:
            d.setdefault(libid.split(":")[0], None)
kicadlibs_syms = {f.stem for f in (root / "KicadLibs/symbols").glob("*.kicad_sym")}
kicadlibs_fps = {f.stem for f in (root / "KicadLibs/footprints").glob("*.pretty")}
lines = ["(sym_lib_table", "\t(version 7)"]
for n in sorted(sym_libs):
    if n == "Senario":
        uri = "${KIPRJMOD}/lib/Senario.kicad_sym"
    elif n in kicadlibs_syms:
        uri = f"{rel}/symbols/{n}.kicad_sym"
    else:
        uri = f"{stock_s}/{n}.kicad_sym"
    lines.append(f'\t(lib (name "{n}") (type "KiCad") (uri "{uri}") (options "") (descr ""))')
for n in ("power",):
    if n not in sym_libs:
        lines.append(f'\t(lib (name "{n}") (type "KiCad") (uri "{stock_s}/{n}.kicad_sym") (options "") (descr ""))')
lines.append(")")
(out / "sym-lib-table").write_text("\n".join(lines) + "\n")
lines = ["(fp_lib_table", "\t(version 7)"]
for n in sorted(fp_libs):
    uri = f"{rel}/footprints/{n}.pretty" if n in kicadlibs_fps else f"{stock_f}/{n}.pretty"
    lines.append(f'\t(lib (name "{n}") (type "KiCad") (uri "{uri}") (options "") (descr ""))')
lines.append(")")
(out / "fp-lib-table").write_text("\n".join(lines) + "\n")
pro = {"meta": {"filename": "Senario.kicad_pro", "version": 3}, "board": {"design_settings": {"rules": {"min_clearance": 0.2, "min_copper_edge_clearance": 0.3}}},
       "sheets": [], "text_variables": {}}
(out / "Senario.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")

def sym(name, ref, desc, left, right, w=5.08):
    h = max(len(left), len(right)) * 2.54 / 2 + 2.54
    def pin(side, i, n):
        y = (len(side_list[side]) - 1) * 1.27 - i * 2.54
        x, a = (-(w + 2.54), 0) if side == "L" else ((w + 2.54), 180)
        return (f'\t\t\t(pin passive line\n\t\t\t\t(at {x} {y:.2f} {a})\n\t\t\t\t(length 2.54)\n'
                f'\t\t\t\t(name "{n[1]}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n'
                f'\t\t\t\t(number "{n[0]}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)\n')
    side_list = {"L": left, "R": right}
    s = f'\t(symbol "{name}"\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
    for k, v, y, hide in (("Reference", ref, h + 1.27, False), ("Value", name, -h - 1.27, False), ("Footprint", "", 0, True),
                          ("Datasheet", "", 0, True), ("Description", desc, 0, True)):
        s += (f'\t\t(property "{k}" "{v}"\n\t\t\t(at 0 {y:.2f} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
              + ("\t\t\t\t(hide yes)\n" if hide else "") + "\t\t\t)\n\t\t)\n")
    s += (f'\t\t(symbol "{name}_0_1"\n\t\t\t(rectangle\n\t\t\t\t(start {-w} {h:.2f})\n\t\t\t\t(end {w} {-h:.2f})\n'
          '\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n')
    s += f'\t\t(symbol "{name}_1_1"\n'
    for i, n in enumerate(left):
        s += pin("L", i, n)
    for i, n in enumerate(right):
        s += pin("R", i, n)
    s += "\t\t)\n\t\t(embedded_fonts no)\n\t)\n"
    return s


lib = ('(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "senario_gen")\n\t(generator_version "1.0")\n'
       + sym("SW_Tact_LED_6pin", "SW", "Tact switch with LED on top, one symbol pin per footprint pad: 1-2 and 3-4 are the two switch contacts, 5 = LED cathode, 6 = LED anode",
             [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4")], [("6", "A"), ("5", "K")])
       + sym("Jack_TRS", "J", "3.5 mm TRS jack, pin numbers = pads of the 4ms PJ366ST footprint (1 tip, 2 sleeve, 3 ring: check on the real part)",
             [("1", "T"), ("3", "R"), ("2", "S")], [])
       + ")\n")
(out / "lib").mkdir(exist_ok=True)
(out / "lib" / "Senario.kicad_sym").write_text(lib)
print("project files written")
