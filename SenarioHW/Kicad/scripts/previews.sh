#!/bin/sh
# Schematic PDF and board previews (front, back) into SenarioHW/docs/previews. Needs KiCad 10 and poppler (pdftoppm).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; KDIR="$(dirname "$HERE")"; DOCS="$KDIR/../docs"
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
mkdir -p "$DOCS/previews"
cd "$KDIR"
$K sch export pdf -o "$DOCS/previews/Senario_schematic.pdf" Senario.kicad_sch >/dev/null 2>&1
$K pcb export pdf --layers "F.Cu,F.SilkS,F.CrtYd,Edge.Cuts,Dwgs.User" -o /tmp/senario_front.pdf Senario.kicad_pcb >/dev/null 2>&1
$K pcb export pdf --layers "B.Cu,B.SilkS,B.CrtYd,Edge.Cuts" --mirror -o /tmp/senario_back.pdf Senario.kicad_pcb >/dev/null 2>&1
pdftoppm -r 150 -png -singlefile /tmp/senario_front.pdf "$DOCS/previews/pcb_front"
pdftoppm -r 150 -png -singlefile /tmp/senario_back.pdf "$DOCS/previews/pcb_back"
python3 -I "$HERE/gen_bom.py" "$DOCS/bom.csv"
