#!/usr/bin/env python3
"""Show or hide the faceplate 3D model of FACEPLATE1 in Senario.kicad_pcb (a text edit of the model's (hide yes) flag). Usage: faceplate_toggle.py on|off"""
import re, sys
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "Senario.kicad_pcb"
t = path.read_text()
pat = re.compile(r'(\(model "\$\{KIPRJMOD\}/models/Faceplate_24HP\.step"\n)(\t*\(hide yes\)\n)?')
if not pat.search(t):
    sys.exit("no FACEPLATE1 model on the board: run scripts/build.sh")
indent = "\t" * 4
t = pat.sub(lambda m: m.group(1) + ("" if sys.argv[1] == "on" else indent + "(hide yes)\n"), t, count=1)
path.write_text(t)
