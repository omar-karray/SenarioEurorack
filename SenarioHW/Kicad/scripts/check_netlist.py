#!/usr/bin/env python3
"""Compare the schematic's netlist (kicad-cli XML) with the nets on the PCB pads. Run with KiCad's Python."""
import sys, xml.etree.ElementTree as ET
import pcbnew

xml, pcb = sys.argv[1], sys.argv[2]
sch = {}
for n in ET.parse(xml).getroot().iter("net"):
    name = n.get("name").lstrip("/")
    for node in n.iter("node"):
        sch[(node.get("ref"), node.get("pin"))] = name
b = pcbnew.LoadBoard(pcb)
pcbn = {}
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname():
            pcbn[(fp.GetReference(), p.GetNumber())] = p.GetNetname().lstrip("/")
bad = []
for k, v in pcbn.items():
    s = sch.get(k)
    if s != v:
        bad.append((k, "pcb=" + v, "sch=" + str(s)))
# schematic connections whose footprint pad is missing on the PCB (ignore symbol-only parts)
refs = {fp.GetReference() for fp in b.GetFootprints()}
miss = [k for k in sch if k[0] in refs and k not in pcbn and not k[0].startswith("#")]
print(f"pcb pads with nets: {len(pcbn)}; schematic pins: {len(sch)}")
print("mismatches:", len(bad))
for x in bad[:15]: print("  ", x)
print("schematic pins without a net on the PCB:", len(miss)); print("  ", miss[:15])
