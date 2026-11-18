#!/usr/bin/env python3
"""Which pad of each Boomele 2x5 socket touches which pad of the Seed2 DFM (seed_sockets.json).

The Seed sits on the back side, so the geometry is computed for the flipped (bottom) footprints. The map is a fact of the
two footprints, invariant under rotating the whole assembly; gen_schematic wires the socket pins with it and gen_pcb places the
sockets so that pad n really touches the Seed pad of the map. Run with KiCad's Python (rarely: only if a footprint changes).
"""
import json, sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent
LIBS = HERE.parents[2] / "KicadLibs" / "footprints"
b = pcbnew.BOARD()
f = lambda v: round(pcbnew.ToMM(v), 3)


def load(lib, name, rot):
    fp = pcbnew.FootprintLoad(str(LIBS / f"{lib}.pretty"), name)
    b.Add(fp)
    try:
        fp.Flip(pcbnew.VECTOR2I(0, 0), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    except Exception:
        fp.Flip(pcbnew.VECTOR2I(0, 0), True)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    return {p.GetNumber(): (f(p.GetPosition().x), f(p.GetPosition().y)) for p in fp.Pads()}


seed = load("Daisy-Boards", "DAISY_SEED2_DFM", 0)
out = {}
for letter in "ABCDE":
    bank = {n: xy for n, xy in seed.items() if n[0] == letter}
    assert len(bank) == 10, (letter, len(bank))
    found = None
    for rot in (0, 90, 180, 270):
        sock = load("Daisy_Seed_Misc", "PinSocket_2x05_P1.27mm_SMD_Boomele_C59983", rot)
        for cand, cxy in sorted(bank.items()):
            tx, ty = cxy[0] - sock["1"][0], cxy[1] - sock["1"][1]
            m = {}
            for n, (x, y) in sock.items():
                hit = [k for k, (bx, by) in bank.items() if abs(bx - (x + tx)) < 0.15 and abs(by - (y + ty)) < 0.15]
                if len(hit) != 1:
                    break
                m[n] = hit[0]
            else:
                if len(set(m.values())) == 10:
                    found = (rot, m)
                    break
        if found:
            break
    assert found, f"no fit for bank {letter}"
    out[letter] = {"map": {k: found[1][k] for k in sorted(found[1], key=int)}}
    print(letter, "rot", found[0], out[letter]["map"])
(HERE / "seed_sockets.json").write_text(json.dumps(out, indent=1) + "\n")
