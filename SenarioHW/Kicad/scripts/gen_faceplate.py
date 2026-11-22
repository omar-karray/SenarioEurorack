#!/usr/bin/env python3
"""Faceplate for the 3D view: a 24HP Eurorack panel (121.5 x 128.5 mm) as a JLCPCB faceplate PCB (1.6 mm, grey aluminium look: light grey mask, black silkscreen lettering) with a cutout for every front control,
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
Z_PANEL = 10.0                                 # underside of the panel above the board. 10.0 since 2026-11-22 (the Alpha RD901F pot: shoulder at 10.0, does not fit under 9.0; spec-beta.md section 3). Was 9.0, the housing top of the Thonkiconn jacks (Thonk drawing + 3D model): at 10.0 the jacks stand 1.0 mm below the panel, their bushing (5.5 above the housing) still passes it
sys.path.insert(0, str(Path(__file__).parent))
import design as D
BOARD_W, BOARD_H = D.BOARD["w"], D.BOARD["h"]
X0, Y0 = (BOARD_W - PANEL_W) / 2, (BOARD_H - PANEL_H) / 2     # panel top-left corner in board coordinates
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
sys.path.insert(0, str(Path(__file__).parent))
import design as D
OLED_WINDOW = D.OLED_WINDOW                      # w, h and the centre in the module frame (viewing area + margins; follows design.OLED_MODEL)

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

    def opening_of(f):
        """The footprint's own hidden property Faceplate_Opening ("round D" or "rect W H", centred on its origin, sized from the part's cap): None if it has none."""
        for fld in f.GetFields():
            if fld.GetName() == "Faceplate_Opening":
                w = fld.GetText().split()
                return (w[0], [float(v) for v in w[1:]])
        return None

    mx_pos = []
    for ref, f in sorted(fp.items()):
        x, y = pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y)
        if x > BOARD_W + 1.0:                                # a part parked beside the board (not placed yet, design.PLACED): no cutout
            continue
        deg = f.GetOrientationDegrees()
        op = opening_of(f)
        if ref.startswith("J_OLED"):
            w, h, ox, oy = OLED_WINDOW
            a = math.radians(deg)
            rect(x + ox * math.cos(a) + oy * math.sin(a), y - ox * math.sin(a) + oy * math.cos(a), w, h, deg)     # KiCad: positive angle = counter-clockwise on screen, y down
            report.append((ref, "OLED window %.1f x %.1f" % (w, h)))
            if D.OLED_ON_FACEPLATE:                              # the module's 4 mounting holes (screws into spacers), same footprint-frame positions as the carrier holes had
                holes, hd = D.OLED_HOLES
                for hx, hy in holes:
                    circle(x + hx * math.cos(a) + hy * math.sin(a), y - hx * math.sin(a) + hy * math.cos(a), hd)
                report.append((ref, "OLED mounting holes 4 x %.1f" % hd))
        elif ref.startswith("J_USB"):
            slot(x, y, D.USB_SLOT_L, 3.8, deg)
            report.append((ref, "USB-C opening %.1f x 3.8" % D.USB_SLOT_L))
        elif ref.startswith("J_SD"):
            a = math.radians(deg)
            ox = 0.4                                          # the slot is centred on the pad row (x -3.45 .. 4.25); y is a guess: check it in the 3D view
            rect(x + ox * math.cos(a), y - ox * math.sin(a), D.SD_SLOT_L, 3.1, deg)
            report.append((ref, "microSD slot %.1f x 3.1 (position approximate)" % D.SD_SLOT_L))
        elif ref.startswith("SW_MX"):
            mx_pos.append((x, y))                            # no cutout of its own: ONE window over the whole matrix (below), no webs between the keys
        elif op and op[0] == "round":
            circle(x, y, op[1][0])
            report.append((ref, "%s round %.1f (Faceplate_Opening)" % (ref, op[1][0])))
        elif op and op[0] == "rect":
            rect(x, y, op[1][0], op[1][1], deg)
            report.append((ref, "%s rect %.1f x %.1f (Faceplate_Opening)" % (ref, op[1][0], op[1][1])))
        elif ref.startswith("J_") and not ref.startswith(("J_PWR", "J_SEED")):
            circle(x, y, 6.2)
            report.append((ref, "jack dia 6.2"))
        elif ref.startswith("PTL"):
            slot(x, y, 23.6, 3.6, deg)                       # travel 20 + lever 3.0
            report.append((ref, "PTL slot 23.6 x 3.6"))
        elif ref == "SL1":
            slot(x, y, 65.5, 3.0, deg)                       # travel 60 + lever 5
            report.append((ref, "Alps slot 65.5 x 3.0"))
        elif ref in ("SW_BTN9", "SW_BTN10"):
            circle(x, y, 9.6)
            report.append((ref, "TL16 cap dia 9.6"))
        elif ref.startswith("SW_BTN"):
            circle(x, y, 6.0)
            report.append((ref, "TL1 cap dia 6.0"))
        elif ref.startswith("ENC"):
            circle(x, y, 7.4)
            report.append((ref, "encoder dia 7.4"))
        elif ref.startswith("VR"):
            circle(x, y, 7.0)
            report.append((ref, "pot dia 7.0"))

    if mx_pos:                                           # one rectangular window for the whole MX matrix: the caps (MX_CAP wide) at the outer keys + 0.3 mm each side
        xs, ys = [q[0] for q in mx_pos], [q[1] for q in mx_pos]
        w_, h_ = max(xs) - min(xs) + D.MX_CAP + 0.6, max(ys) - min(ys) + D.MX_CAP + 0.6
        rect((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, w_, h_)
        report.append(("SW_MX", "MX window %.1f x %.1f over %d keys (one cutout, no webs)" % (w_, h_, len(mx_pos))))

    # ---- LEGENDS (F.SilkS = the black lettering on the grey plate). Positions are relative to each part's cutout; the text is a first pass (the functions of the buttons / pots / sliders are not decided:
    # they carry their schematic numbers). Edit LABELS here. Text is centred; size in mm.
    def label(s, x, y, size=1.1, angle=0.0):
        tx = pcbnew.PCB_TEXT(b)
        tx.SetText(s)
        tx.SetLayer(pcbnew.F_SilkS)
        tx.SetPosition(V(x, y))
        tx.SetTextSize(V(size, size))
        tx.SetTextThickness(mm(max(0.12, size * 0.14)))
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        tx.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        if angle:
            tx.SetTextAngleDegrees(angle)
        b.Add(tx)

    def pos(ref):
        f = fp.get(ref)
        if f is None:
            return None
        x, y = pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y)
        return None if x > BOARD_W + 1.0 else (x, y)

    JACK_TXT = {"AIN1": "1", "AIN2": "2", "AIN3": "3", "AIN4": "4", "CVIN1": "1", "CVIN2": "2", "CVIN3": "3", "CVIN4": "4",
                "AOUT1": "L", "AOUT2": "R", "AOUT3": "L", "AOUT4": "R", "CVOUT1": "1", "CVOUT2": "2", "GATEOUT1": "1", "GATEOUT2": "2",
                "GATEIN1": "GATE IN", "GATEIN2": "GATE IN", "CLKIN": "CLK IN", "CLKOUT": "CLK OUT", "MIDIIN1": "MIDI IN", "MIDIOUT1": "MIDI OUT"}
    for n, s in JACK_TXT.items():
        q = pos("J_" + n)
        if q:
            label(s, q[0], q[1] + 5.4)
    # column headings above the first jack row
    def jx(n):
        return pos("J_" + n)[0]
    for s, ns in (("AUDIO IN", ("AIN1", "AIN3")), ("CV IN", ("CVIN1", "CVIN3"))):
        label(s, sum(jx(n) for n in ns) / 2, 2.2, 1.0)
    for s, n in (("SEND OUT", "AOUT3"), ("MAIN OUT", "AOUT1"), ("CV OUT", "CVOUT1"), ("GATE OUT", "GATEOUT1")):
        label(s, jx(n), 2.2, 1.0)
    for i in range(1, 5):                                           # encoders: under the knob (knob radius about 7.5)
        q = pos(f"ENC{i}")
        if q:
            label(f"ENC {i}", q[0], q[1] + 8.4)
    for ref, s, dy in (("VR1", "TRIM 1", 6.2), ("VR2", "TRIM 2", 6.2), ("VR3", "POT 1", 7.6), ("VR4", "POT 2", 7.6)):
        q = pos(ref)
        if q:
            label(s, q[0], q[1] + dy)
    for ref, s in (("PTL1", "SLIDE 1"), ("PTL2", "SLIDE 2")):       # above the slot
        q = pos(ref)
        if q:
            label(s, q[0], q[1] - 11.8 - 2.4)
    q = pos("SL1")
    if q:
        label("SLIDE 3", q[0], q[1] - 3.4)
    for i in range(1, 7):                                           # the six control buttons: above the caps
        q = pos(f"SW_BTN{i}")
        if q:
            label(f"BTN {i}", q[0], q[1] - 5.2)
    for ref, s, dy in (("SW_BTN7", "BTN 7", -5.2), ("SW_BTN8", "BTN 8", -5.2), ("SW_BTN9", "A", 7.2), ("SW_BTN10", "B", 7.2)):
        q = pos(ref)
        if q:
            label(s, q[0], q[1] + dy, 1.1 if len(s) > 1 else 1.6)
    q = pos("J_USB1")
    if q:
        label("USB", q[0], q[1] + D.USB_SLOT_L / 2 + 1.8)
    q = pos("J_SD1")
    if q:
        label("SD", q[0] - 0.55, q[1] - 0.4 + D.SD_SLOT_L / 2 + 1.8)
    # the title in the rails (the panel is 10.25 mm taller than the board at the top and the bottom)
    label("SENARIO", BOARD_W / 2, -5.0, 4.0)
    label("LOOPER  /  MULTIFX", BOARD_W / 2, BOARD_H + 5.0, 2.2)
    report.append(("legends", "text on F.SilkS: jacks, headings, encoders, pots, sliders, buttons, title"))

    out_dir = KDIR / "faceplate"
    out_dir.mkdir(exist_ok=True)
    pcbnew.SaveBoard(str(out_dir / "Faceplate.kicad_pcb"), b)
    import re as _re
    txt = (out_dir / "Faceplate.kicad_pcb").read_text()
    stack = ('\t\t(stackup\n\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "Black"))\n\t\t\t(layer "F.Paste" (type "Top Solder Paste"))\n'
             '\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "#6F747AFF") (thickness 0.01))\n\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))\n'
             '\t\t\t(layer "dielectric 1" (type "core") (color "FR4 natural") (thickness 1.53) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))\n'
             '\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))\n\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "#6F747AFF") (thickness 0.01))\n'
             '\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))\n\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "Black"))\n'
             '\t\t\t(copper_finish "None")\n\t\t\t(dielectric_constraints no)\n\t\t)\n')
    txt = txt.replace("\t(setup\n", "\t(setup\n" + stack, 1).replace("(thickness 2)", "(thickness 1.6)", 1)
    (out_dir / "Faceplate.kicad_pcb").write_text(txt)
    subprocess.run([KICAD_CLI, "pcb", "export", "step", "--board-only", "--include-soldermask", "--include-silkscreen", "--force", "--user-origin", "0x0mm", "-o", str(step), str(out_dir / "Faceplate.kicad_pcb")],
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
