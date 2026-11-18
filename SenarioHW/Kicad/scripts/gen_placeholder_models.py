#!/usr/bin/env python3
"""Simple 3D placeholder bodies (VRML, mm) for parts without a public model: Bourns PTL20, Alps RS6011, the OLED module.

Sizes: PTL body from the footprint outline and the Bourns datasheet (6.0 mm above the board, lever not drawn); RS6011 body 75 x 9 x 7 mm from the Alps drawing
(lever not drawn); OLED module on its header, bottom 8.5 mm above the board (as the Tanghim board; CHECK the standoff you use). Replace with real models when you have them.
Write: SenarioHW/Kicad/models/*.wrl. Units are mm: the footprints reference them with scale 1/2.54 (KiCad reads VRML in 0.1 inch units).
"""
import sys
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(exist_ok=True)


def box(cx, cy, z0, w, d, h, rgb):
    """Box centred at (cx, cy) in model coordinates (y up = -y of the PCB), from z0 to z0 + h."""
    return (f"Transform {{ translation {cx} {cy} {z0 + h / 2}\n  children [ Shape {{ appearance Appearance {{ material Material {{ diffuseColor {rgb[0]} {rgb[1]} {rgb[2]} }} }}\n"
            f"    geometry Box {{ size {w} {d} {h} }} }} ] }}\n")


def write(name, parts):
    (out / name).write_text("#VRML V2.0 utf8\n" + "".join(box(*p) for p in parts))


# Bourns PTL20 (datasheet): body 35.0 x 9.0 x 6.0 mm; lever 3.0 along the travel x 2.05 across, length L = 10 / 15 / 19 mm above the body (15 here:
# CHANGE LEVER_L to your lever), a red lens on the top 6 mm (the LED sits in the lever). Lever drawn at mid travel.
LEVER_L = 15.0
write("PTL20_placeholder.wrl", [
    (0, 0, 0, 35.0, 9.0, 6.0, (0.15, 0.15, 0.17)),
    (0, 0, 6.0, 3.0, 2.05, LEVER_L - 6.0, (0.1, 0.1, 0.12)),
    (0, 0, 6.0 + LEVER_L - 6.0, 3.0, 2.05, 6.0, (0.85, 0.1, 0.1)),
])
# Alps RS6011: body 75 x 9 x 7 mm; lever about 4 x 2 mm up to 15 mm above the board (style 17 drawing; the lever length is a customer option)
write("Alps_RS6011_placeholder.wrl", [
    (0, 0, 0, 75.0, 9.0, 7.0, (0.62, 0.62, 0.65)),
    (0, 0, 7.0, 4.0, 2.0, 8.0, (0.2, 0.2, 0.22)),
])
# OLED: footprint origin = pin 1; module x -6.03 .. 21.27, y(PCB) -1.32 .. 26.48 -> model y = -y(PCB); glass centre x 7.62, y(PCB) 3.55 .. 20.45
write("OLED_HS96L01_placeholder.wrl", [
    (7.62, -12.58, 8.5, 27.3, 27.8, 1.2, (0.05, 0.25, 0.1)),
    (7.62, -12.0, 9.7, 24.74, 16.9, 1.4, (0.02, 0.02, 0.03)),
])


def cyl(r, z0, z1, rgb, n=24):
    """Cylinder along z from z0 to z1, as an n-sided prism (KiCad's VRML reader ignores Cylinder)."""
    import math
    pts = []
    for z in (z0, z1):
        for k in range(n):
            a = 2 * math.pi * k / n
            pts.append(f"{r * math.cos(a):.3f} {r * math.sin(a):.3f} {z}")
    idx = []
    for k in range(n):
        k2 = (k + 1) % n
        idx.append(f"{k}, {k2}, {n + k2}, {n + k}, -1")
    idx.append(", ".join(str(k) for k in reversed(range(n))) + ", -1")
    idx.append(", ".join(str(n + k) for k in range(n)) + ", -1")
    return (f"Shape {{ appearance Appearance {{ material Material {{ diffuseColor {rgb[0]} {rgb[1]} {rgb[2]} }} }}\n"
            f"  geometry IndexedFaceSet {{ solid FALSE coord Coordinate {{ point [ {', '.join(pts)} ] }}\n"
            f"    coordIndex [ {', '.join(idx)} ] }} }}\n")


# Top-Up EC12PL illuminated encoder: body 12.4 x 13.2 x 7.8, M9 bushing 7 long, dia 6 shaft to 25.3 mm (MD-15141)
(out / "Encoder_RGB_TopUp_placeholder.wrl").write_text("#VRML V2.0 utf8\n" + box(0, 0, 0, 12.4, 13.2, 7.8, (0.55, 0.55, 0.58)) +
    cyl(4.5, 7.8, 14.8, (0.65, 0.65, 0.68)) + cyl(3.0, 14.8, 25.3, (0.08, 0.08, 0.1)))
print("wrote placeholders")
