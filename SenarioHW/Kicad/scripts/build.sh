#!/bin/sh
# Regenerate the Senario KiCad project (schematic sheets, PCB placement, project and library tables).
# Needs KiCad 10 (its bundled Python provides pcbnew). Usage: scripts/build.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(dirname "$HERE")"
if [ -e "$OUT/Senario.kicad_pcb" ] && [ -z "$FORCE" ]; then
  echo "Senario.kicad_pcb exists: rebuilding overwrites the schematic AND your hand placement. Run FORCE=1 $0 to do it anyway." >&2
  exit 1
fi
KICAD_PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
python3 -I "$HERE/gen_placeholder_models.py" "$OUT/models"
python3 -I "$HERE/gen_project.py" "$OUT"
python3 -I "$HERE/gen_schematic.py" "$OUT"
"$KICAD_PY" -I "$HERE/gen_pcb.py" "$OUT/Senario.kicad_pcb" 2>&1 | grep -v 'wxApp'
for try in 1 2 3; do                                                  # pcbnew crashes now and then when it saves a board: retry
  if "$KICAD_PY" -I "$HERE/gen_faceplate.py" 2>&1 | grep -v 'wxApp' | grep -q 'FACEPLATE1 on the board'; then echo "faceplate ok"; break; fi
  [ "$try" = 3 ] && { echo "gen_faceplate.py failed 3 times" >&2; exit 1; }
done
