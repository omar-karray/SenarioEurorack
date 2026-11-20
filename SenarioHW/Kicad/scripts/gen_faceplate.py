#!/usr/bin/env python3
"""Faceplate for the 3D view: a 24HP Eurorack panel (121.5 x 128.5 mm) as a JLCPCB faceplate PCB (1.6 mm, black solder mask) with a cutout for every front control,
its underside on the housing top of the Thonkiconn jacks.

Run with KiCad's Python from SenarioHW/Kicad, after gen_pcb.py:  gen_faceplate.py   (it re-runs itself as "gen_faceplate.py place" in a second process:
saving the main board while the plate board object is alive crashes pcbnew from time to time)

1. Reads the front-side footprints of Senario.kicad_pcb (final positions) and builds faceplate/Faceplate.kicad_pcb: the panel outline and the cutouts
   as Edge.Cuts shapes, board thickness = PANEL_T. (The same file is the starting point of a real panel: a faceplate PCB, or Edge.Cuts to DXF.)
2. kicad-cli exports it to models/Faceplate_24HP.step (board only, origin = the board origin, so panel coordinates = board coordinates).
3. Adds the footprint FACEPLATE1 to Senario.kicad_pcb: no pads, only that 3D model, lifted to Z_PANEL (the panel underside = the seat of the jacks).

The panel is centred on the 120 x 108 board: 0.75 mm wider on each side, 10.25 mm taller at the top and the bottom (the rails). Panel mounting holes:
dia 3.2, 3 mm from the top and bottom edge, 7.5 mm from the left edge and 21 HP x 5.08 mm further right (Doepfer).
Cutout sizes (edit below; the sources are in docs/faceplate.md): jacks 6.2, pots 7.0, encoders 9.2, MX 14 x 14, K6 buttons 10.5, HOOYA caps 5.8, PTL slots, Alps slot,
OLED viewing window, USB-C opening.
"""
import math, subprocess, sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent
KDIR = HERE.parent
PANEL_W, PANEL_H, PANEL_T = 121.5, 128.5, 1.6     # a standard 1.6 mm PCB
Z_PANEL = 9.0                                  # underside of the panel above the board: the housing top of the Thonkiconn jacks (Thonk drawing: housing 9.0 along the barrel, bushing 5.5 more; same on the 3D model)
BOARD_W, BOARD_H = 120.0, 108.0
X0, Y0 = (BOARD_W - PANEL_W) / 2, (BOARD_H - PANEL_H) / 2     # panel top-left corner in board coordinates
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
OLED_WINDOW = (24.0, 12.8, 7.62, 10.21)         # w, h and the centre in the module frame (viewing area 22.74 x 11.86 + 0.6 each side)

step = KDIR / "models" / "Faceplate_24HP.step"
PLACE = len(sys.argv) > 1 and sys.argv[1] == "place"
src = pcbnew.LoadBoard(str(KDIR / "Senario.kicad_pcb"))
fp = {f.GetReference(): f for f in src.GetFootprints() if f.GetLayerName() == "F.Cu"}

if not PLACE:
    b = pcbnew.BOARD()
    

    def shape(kind):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(kind)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        b.Add(s)
        return s


    def circle(cx, cy, d):
        s = shape(pcbnew.SHAPE_T_CIRCLE)
        s.SetCenter(V(cx, cy))
        s.SetEnd(V(cx + d / 2, cy))


    def rect(cx, cy, w, h, deg=0.0):
        a = math.radians(deg)
        pts = []
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x, y = sx * w / 2, sy * h / 2
            pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
        for i in range(4):
            s = shape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(V(*pts[i]))
            s.SetEnd(V(*pts[(i + 1) % 4]))


    def slot(cx, cy, length, width, deg=0.0):
        """Stadium: overall length x width, long axis at deg (0 = along x)."""
        a = math.radians(deg)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        r = width / 2
        h = length / 2 - r
        p1 = (cx - ux * h, cy - uy * h)
        p2 = (cx + ux * h, cy + uy * h)
        for (px, py), (qx, qy) in (((p1[0] + nx * r, p1[1] + ny * r), (p2[0] + nx * r, p2[1] + ny * r)),
                                   ((p1[0] - nx * r, p1[1] - ny * r), (p2[0] - nx * r, p2[1] - ny * r))):
            s = shape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(V(px, py))
            s.SetEnd(V(qx, qy))
        for c, sign in ((p2, 1), (p1, -1)):                    # end caps, half circles
            s = shape(pcbnew.SHAPE_T_ARC)
            start = (c[0] + nx * r * sign, c[1] + ny * r * sign)
            end = (c[0] - nx * r * sign, c[1] - ny * r * sign)
            mid = (c[0] + ux * r * sign, c[1] + uy * r * sign)
            s.SetArcGeometry(V(*start), V(*mid), V(*end))


    # panel outline and its 4 mounting holes
    rect(X0 + PANEL_W / 2, Y0 + PANEL_H / 2, PANEL_W, PANEL_H)
    for hx in (X0 + 7.5, X0 + 7.5 + 21 * 5.08):
        for hy in (Y0 + 3.0, Y0 + PANEL_H - 3.0):
            circle(hx, hy, 3.2)

    report = []
    for ref, f in sorted(fp.items()):
        x, y = pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y)
        deg = f.GetOrientationDegrees()
        if ref.startswith("J_OLED"):
            w, h, ox, oy = OLED_WINDOW
            a = math.radians(deg)
            rect(x + ox * math.cos(a) - oy * math.sin(a), y + ox * math.sin(a) + oy * math.cos(a), w, h, deg)
            report.append((ref, "OLED window %.1f x %.1f" % (w, h)))
        elif ref.startswith("J_USB"):
            slot(x, y, 9.4, 3.6, deg)
            report.append((ref, "USB-C opening 9.4 x 3.6"))
        elif ref.startswith("J_") and not ref.startswith(("J_SD", "J_PWR", "J_SEED")):
            circle(x, y, 6.2)
            report.append((ref, "jack dia 6.2"))
        elif ref.startswith("ENC"):
            circle(x, y, 9.2)
            report.append((ref, "encoder dia 9.2"))
        elif ref.startswith("VR"):
            circle(x, y, 7.0)
            report.append((ref, "pot dia 7.0"))
        elif ref.startswith("SW_MX"):
            rect(x, y, 14.0, 14.0)
            report.append((ref, "MX 14 x 14"))
        elif ref.startswith("PTL"):
            slot(x, y, 23.6, 3.6, deg)                       # travel 20 + lever 3.0
            report.append((ref, "PTL slot 23.6 x 3.6"))
        elif ref == "SL1":
            slot(x, y, 65.5, 3.0, deg)                       # travel 60 + lever 5
            report.append((ref, "Alps slot 65.5 x 3.0"))
        elif ref in ("SW_BTN1", "SW_BTN2"):
            circle(x, y, 10.5)
            report.append((ref, "K6 button dia 10.5"))
        elif ref.startswith("SW_BTN"):
            circle(x, y, 5.8)
            report.append((ref, "HOOYA cap dia 5.8"))

    out_dir = KDIR / "faceplate"
    out_dir.mkdir(exist_ok=True)
    pcbnew.SaveBoard(str(out_dir / "Faceplate.kicad_pcb"), b)
    import re as _re
    txt = (out_dir / "Faceplate.kicad_pcb").read_text()
    stack = ('\t\t(stackup\n\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "White"))\n\t\t\t(layer "F.Paste" (type "Top Solder Paste"))\n'
             '\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))\n\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))\n'
             '\t\t\t(layer "dielectric 1" (type "core") (color "FR4 natural") (thickness 1.53) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))\n'
             '\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))\n\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))\n'
             '\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))\n\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))\n'
             '\t\t\t(copper_finish "None")\n\t\t\t(dielectric_constraints no)\n\t\t)\n')
    txt = txt.replace("\t(setup\n", "\t(setup\n" + stack, 1).replace("(thickness 2)", "(thickness 1.6)", 1)
    (out_dir / "Faceplate.kicad_pcb").write_text(txt)
    subprocess.run([KICAD_CLI, "pcb", "export", "step", "--board-only", "--include-soldermask", "--force", "--user-origin", "0x0mm", "-o", str(step), str(out_dir / "Faceplate.kicad_pcb")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([sys.executable, str(Path(__file__).resolve()), "place"], check=True)

if PLACE:
    import re, uuid
    # the exported plate is a little thicker than PANEL_T (soldermask faces included): scale z to the exact thickness
    zs = [float(m[2]) for m in re.findall(r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*\)", step.read_text(errors="ignore"))]
    Z_SCALE = PANEL_T / (max(zs) - min(zs))
    Z_OFFSET = Z_PANEL - min(zs) * Z_SCALE                     # the exported plate starts a little below 0 (solder mask): put its underside exactly at Z_PANEL
    lib = KDIR / "lib" / "Senario.pretty"
    lib.mkdir(parents=True, exist_ok=True)
    (lib / "Faceplate_24HP.kicad_mod").write_text(
        '(footprint "Faceplate_24HP"\n\t(version 20260206)\n\t(generator "pcbnew")\n\t(generator_version "10.0")\n\t(layer "F.Cu")\n'
        '\t(descr "Faceplate 24HP, 1.6 mm black PCB on the jack housings: 3D model only (generated by gen_faceplate.py)")\n'
        f'\t(property "Reference" "FACEPLATE1"\n\t\t(at 0 0 0)\n\t\t(layer "F.SilkS")\n\t\t(hide yes)\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n'
        f'\t(property "Value" "Faceplate 24HP"\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n\t\t(hide yes)\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n'
        '\t(attr exclude_from_pos_files exclude_from_bom)\n'
        f'\t(model "${{KIPRJMOD}}/models/Faceplate_24HP.step"\n\t\t(offset\n\t\t\t(xyz 0 0 {Z_OFFSET:.4f})\n\t\t)\n\t\t(scale\n\t\t\t(xyz 1 1 {Z_SCALE:.6f})\n\t\t)\n\t\t(rotate\n\t\t\t(xyz 0 0 0)\n\t\t)\n\t)\n'
        '\t(embedded_fonts no)\n)\n')
    if src.FindFootprintByReference("FACEPLATE1") is None:      # (never remove and re-add: that crashes pcbnew; gen_pcb.py starts from a fresh board)
        n = pcbnew.FootprintLoad(str(lib), "Faceplate_24HP")
        n.SetReference("FACEPLATE1")
        n.SetPosition(V(0, 0))
        src.Add(n)
        pcbnew.SaveBoard(str(KDIR / "Senario.kicad_pcb"), src)
    print("faceplate: footprint FACEPLATE1 on the board, z scale %.4f" % Z_SCALE)
else:
    print("faceplate:", len(report), "cutouts,", step.name)
