#!/usr/bin/env python3
"""BOM (one row per part) from design.py: SenarioHW/docs/bom.csv. Hand = soldered by hand, front side; SMD = back side (JLCPCB)."""
import csv, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import design as D
out = Path(sys.argv[1])
rows = {}
for p in D.PARTS:
    if not p["fp"] or p["sym"].startswith("Mechanical") or D.pcb_hidden(p):
        continue
    key = (p["value"], p["fp"], p["props"].get("LCSC", ""), "hand" if p["side"] == "T" else "smd")
    rows.setdefault(key, []).append(p["ref"])
rows[("Daisy Seed2 DFM (Electrosmith, bought; plugs into J_SEED_A..E)", "module", "", "purchased")] = ["U_SEED1"]
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Value", "Footprint", "LCSC", "Assembly", "Qty", "Designators"])
    for (v, fp, l, a), refs in sorted(rows.items(), key=lambda kv: (kv[0][3], kv[0][1], kv[0][0])):
        w.writerow([v, fp, l, a, len(refs), " ".join(refs)])
print(len(rows), "BOM lines,", sum(len(r) for r in rows.values()), "parts")
