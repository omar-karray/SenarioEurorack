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


write("PTL20_placeholder.wrl", [(0, 0, 0, 35.24, 9.24, 6.0, (0.15, 0.15, 0.17))])
write("Alps_RS6011_placeholder.wrl", [(0, 0, 0, 75.0, 9.0, 7.0, (0.62, 0.62, 0.65))])
# OLED: footprint origin = pin 1; module x -6.03 .. 21.27, y(PCB) -1.32 .. 26.48 -> model y = -y(PCB); glass centre x 7.62, y(PCB) 3.55 .. 20.45
write("OLED_HS96L01_placeholder.wrl", [
    (7.62, -12.58, 8.5, 27.3, 27.8, 1.2, (0.05, 0.25, 0.1)),
    (7.62, -12.0, 9.7, 24.74, 16.9, 1.4, (0.02, 0.02, 0.03)),
])
print("wrote placeholders")
