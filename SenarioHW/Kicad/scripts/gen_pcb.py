#!/usr/bin/env python3
"""Write Senario.kicad_pcb (primary placement, unrouted) from design.py.

Run with KiCad's Python:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 gen_pcb.py <out.kicad_pcb>

Front (top) side: the hand-soldered controls at the fixed floorplan positions (design.FLOOR).
Back (bottom) side: the Seed2 DFM, every IC and every SMD part, placed automatically next to the parts they connect to,
without overlapping each other or the through-hole pads.
"""
import math
import sys
from collections import defaultdict
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import design as D
from gen_schematic import POWER_NETS, sym, resolve_pins, expand_unused_units  # same pin resolution as the schematic

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FP_DIRS = [ROOT / "KicadLibs" / "footprints", Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")]
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
tomm = pcbnew.ToMM
RAIL_NETS = POWER_NETS | {"+12V_IN", "-12V_IN", "+12V_FB", "-12V_FB", "-10V_REF", "DSY_VIN", "VCOM_SEED", "VCOM_EXT"}

board = pcbnew.BOARD()
_nets = {}


def net(name):
    if name not in _nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        _nets[name] = n
    return _nets[name]


_cache = {}


def load_fp(fpid):
    lib, name = fpid.split(":", 1)
    for d in FP_DIRS:
        if (d / f"{lib}.pretty").exists():
            fp = pcbnew.FootprintLoad(str(d / f"{lib}.pretty"), name)
            if fp is not None:
                fp.SetFPID(pcbnew.LIB_ID(lib, name))
                return fp
    raise FileNotFoundError(fpid)


_scratch = pcbnew.BOARD()


def place(fp, x, y, rot, bottom):
    if bottom:
        try:
            fp.Flip(V(0, 0), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        except Exception:
            fp.Flip(V(0, 0), True)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(V(x, y))


def apply_models(fp, fpid, ref=None):
    """Point the footprint's 3D models at KicadLibs/3dmodels (see design.MODEL_*), or give it the model of design.MODEL_OVERRIDE."""
    if ref in D.MODEL_BY_REF or fpid in D.MODEL_OVERRIDE:
        f, off, rot, sc = D.MODEL_BY_REF[ref] if ref in D.MODEL_BY_REF else D.MODEL_OVERRIDE[fpid]
        fp.Models().clear()
        m = pcbnew.FP_3DMODEL()
        m.m_Filename = f
        m.m_Offset = pcbnew.VECTOR3D(*off)
        m.m_Rotation = pcbnew.VECTOR3D(*rot)
        m.m_Scale = pcbnew.VECTOR3D(*sc)
        m.m_Show = True
        fp.Models().append(m)
        return
    models = list(fp.Models())
    fp.Models().clear()
    for m in models:
        for a, b in D.MODEL_PATH_REMAP.items():
            if m.m_Filename.startswith(a):
                m.m_Filename = b + m.m_Filename[len(a):]
        fp.Models().append(m)


def geometry(fpid, bottom, rot):
    """Bounding box (courtyard + pads) and pad rectangles of a footprint at the origin, as placed."""
    key = (fpid, bottom, rot)
    if key not in _cache:
        fp = load_fp(fpid)
        _scratch.Add(fp)
        place(fp, 0, 0, rot, bottom)
        layer = pcbnew.B_CrtYd if bottom else pcbnew.F_CrtYd
        bb = fp.GetCourtyard(layer).BBox()
        pads = []
        for p in fp.Pads():
            b = p.GetBoundingBox()
            tht = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) or p.HasHole()
            pads.append((tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom()), tht))
        if bb.GetWidth() > 0:
            box = [tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom())]
        else:
            b = fp.GetBoundingBox(False)
            box = [tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom())]
        for q in pads:
            box = [min(box[0], q[0]), min(box[1], q[1]), max(box[2], q[2]), max(box[3], q[3])]
        _cache[key] = (box, pads)
    return _cache[key]


class Grid:
    """Rectangles in a hash grid for quick overlap queries."""

    def __init__(self, cell=5.0):
        self.cell = cell
        self.g = defaultdict(list)

    def add(self, r):
        c = self.cell
        for i in range(int(r[0] // c), int(r[2] // c) + 1):
            for j in range(int(r[1] // c), int(r[3] // c) + 1):
                self.g[(i, j)].append(r)

    def hit(self, r):
        c = self.cell
        for i in range(int(r[0] // c), int(r[2] // c) + 1):
            for j in range(int(r[1] // c), int(r[3] // c) + 1):
                for o in self.g.get((i, j), ()):
                    if r[0] < o[2] and r[2] > o[0] and r[1] < o[3] and r[3] > o[1]:
                        return True
        return False


def infl(r, m):
    return (r[0] - m, r[1] - m, r[2] + m, r[3] + m)


def shift(r, x, y):
    return (r[0] + x, r[1] + y, r[2] + x, r[3] + y)


def build(out):
    W, H = D.BOARD["w"], D.BOARD["h"]
    # ---- edge cuts
    for (a, b) in (((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a)); s.SetEnd(V(*b))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        board.Add(s)

    parts = [p for p in D.PARTS if p["fp"] and not D.pcb_hidden(p)]
    pos = {}                                  # ref -> (x, y)
    sheet_nets = {}
    # nets per part
    for p in parts:
        s = sym(p["sym"])
        nets = resolve_pins(p, s)
        expand_unused_units(p, s, nets)
        p["_nets"] = nets
        p["_sym"] = s
    netparts = defaultdict(list)
    for p in parts:
        for num, n in p["_nets"].items():
            if n:
                netparts[n].append(p["ref"])

    def make(p, x, y, rot, bottom):
        fp = load_fp(p["fp"])
        board.Add(fp)
        place(fp, x, y, rot, bottom)
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        for k, v in p["props"].items():
            fp.SetField(k, v)
        apply_models(fp, p["fp"], p["ref"])
        fp.Reference().SetTextSize(V(0.8, 0.8)); fp.Reference().SetTextThickness(mm(0.12))
        fp.Value().SetVisible(False)
        if bottom:
            for f in fp.GetFields():
                f.SetMirrored(True)
        if p["ref"].startswith(("SW_MX", "J_SEED")):    # MX: the LED sits in the window; sockets: the module outline covers them
            for g in list(fp.GraphicalItems()):
                if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                    fp.Remove(g)
        # nets
        s = p["_sym"]
        for num, n in p["_nets"].items():
            if not n:
                continue
            pins = [q for q in s.pins if q["number"] == num]
            key = num
            pads = p["padmap"].get(num) or p["padmap"].get(pins[0]["name"] if pins else num) or num
            if isinstance(pads, str):
                pads = [pads]
            for pd in pads:
                got = [q for q in fp.Pads() if q.GetNumber() == pd]
                if not got:
                    raise KeyError(f"{p['ref']}: footprint {p['fp']} has no pad {pd} (pin {num})")
                for q in got:
                    q.SetNet(net(n))
        return fp

    tht_obst = Grid()                         # through-hole pads (both sides) and holes
    bot_obst = Grid()                         # placed bottom parts
    top_court = Grid()                        # courtyards of the front parts (for through-hole parts on the back)
    # ---- front side, fixed
    for p in parts:
        if p["side"] != "T":
            continue
        x, y, rot = D.FLOOR[p["ref"]]
        fp = make(p, x, y, rot, False)
        pos[p["ref"]] = (x, y)
        box, pads = geometry(p["fp"], False, rot)
        for q in pads:
            if q[4]:
                tht_obst.add(infl(shift(q[:4], x, y), 0.5))
        top_court.add(infl(shift(box, x, y), 0.2))

    # ---- back side, automatic
    def anchor_of(p):
        cand = []
        for num, n in p["_nets"].items():
            if not n or n in RAIL_NETS or len(netparts[n]) > 14:
                continue
            for r in netparts[n]:
                if r != p["ref"] and r in pos:
                    cand.append(r)
        if cand:
            ic = [r for r in cand if r.startswith("U")]
            return pos[(ic or cand)[0]]
        # power-only part: nearest IC of the same block on a shared rail
        for num, n in p["_nets"].items():
            for r in netparts.get(n, ()):
                if r != p["ref"] and r in pos and r.startswith("U") and r != "U_SEED1":
                    q = next(z for z in parts if z["ref"] == r)
                    if q["block"] == p["block"]:
                        return pos[r]
        return D.ANCHOR.get(p["block"], (54, 62))

    def find(p, anchor, rots, margin=0.35, pad_only=False, step=0.5, rmax=80, body_clear=False):
        ax, ay = anchor
        for rr in range(0, int(rmax / step)):
            r = rr * step
            pts = [(ax, ay)] if rr == 0 else []
            if rr:
                n = max(1, int(8 * r / step))
                for k in range(n):
                    t = 2 * math.pi * k / n
                    pts.append((ax + r * math.cos(t), ay + r * math.sin(t)))
            for (x, y) in pts:
                x = round(x / step) * step
                y = round(y / step) * step
                for rot in rots:
                    box, pads = geometry(p["fp"], True, rot)
                    b = shift(box, x, y)
                    if b[0] < 0.8 or b[1] < 0.8 or b[2] > W - 0.8 or b[3] > H - 0.8:
                        continue
                    if pad_only:
                        ok = True
                        for q in pads:
                            if tht_obst.hit(infl(shift(q[:4], x, y), 0.3)) or (p["ref"] == "J_PWR1" and top_court.hit(shift(q[:4], x, y))):
                                ok = False
                                break
                        if ok and bot_obst.hit(b):
                            ok = False
                        if ok and body_clear and tht_obst.hit(b):
                            ok = False
                    else:
                        ok = not tht_obst.hit(b)
                        if ok:
                            for q in pads:
                                if tht_obst.hit(infl(shift(q[:4], x, y), 0.3)) :
                                    ok = False
                                    break
                        if ok and bot_obst.hit(infl(b, margin)):
                            ok = False
                        if ok:
                            # a body over a drilled pad of a front part is fine for tiny SMD only if no pad touches it
                            pass
                    if ok:
                        return x, y, rot, b
        raise RuntimeError(f"no room for {p['ref']}")

    seed_src = next(q for q in D.PARTS if q["ref"] == "U_SEED1")
    seed_part = dict(seed_src, fp=seed_src["board_fp"], _nets={}, _sym=None, padmap={}, props={})
    parts.append(seed_part)
    def place_seed(p, x, y, rot):
        """3D module footprint (board only) and the five sockets, placed so that socket pad n touches the Seed pad of the map."""
        fp3 = load_fp("Daisy-Boards:DAISY_SEED2_DFM_3D")
        board.Add(fp3)
        place(fp3, x, y, rot, True)
        for g in list(fp3.GraphicalItems()):          # the module hovers 4.3 mm over the front-side leads: no courtyard check
            if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                fp3.Remove(g)
        fp3.SetReference("U_SEED1")
        fp3.SetValue("Daisy Seed2 DFM")
        fp3.Reference().SetVisible(False)
        fp3.Value().SetVisible(False)
        try:
            fp3.SetBoardOnly(True)
        except Exception:
            pass
        tmp = load_fp(p["fp"])                             # landing pattern, only to read the pad positions
        _scratch.Add(tmp)
        place(tmp, x, y, rot, True)
        world = {q.GetNumber(): (tomm(q.GetPosition().x), tomm(q.GetPosition().y)) for q in tmp.Pads()}
        for letter in "ABCDE":
            sp = next(q for q in parts if q["ref"] == f"J_SEED_{letter}")
            mp = D.SEED_SOCKETS[letter]["map"]
            fit = None
            for srot in (0, 90, 180, 270):
                ts = load_fp(sp["fp"])
                _scratch.Add(ts)
                place(ts, 0, 0, srot, True)
                off = {q.GetNumber(): (tomm(q.GetPosition().x), tomm(q.GetPosition().y)) for q in ts.Pads()}
                tx, ty = world[mp["1"]][0] - off["1"][0], world[mp["1"]][1] - off["1"][1]
                if all(abs(world[mp[n]][0] - (off[n][0] + tx)) < 0.15 and abs(world[mp[n]][1] - (off[n][1] + ty)) < 0.15 for n in mp):
                    fit = (tx, ty, srot)
                    break
            if not fit:
                raise RuntimeError(f"socket {letter} does not fit the Seed pads")
            make(sp, fit[0], fit[1], fit[2], True)
            pos[sp["ref"]] = (fit[0], fit[1])

    bottom = [p for p in parts if p["side"] == "B" and p["block"] != "seedsock"]
    order = ([p for p in bottom if p["ref"] == "J_PWR1"] + [p for p in bottom if p["ref"] == "U_SEED1"] +
             [p for p in bottom if p["ref"].startswith("U") and p["ref"] != "U_SEED1"] +
             [p for p in bottom if not p["ref"].startswith("U") and p["ref"] != "J_PWR1"])
    report = []
    for p in order:
        anchor = D.ANCHOR.get(p["block"], (54, 62)) if p["ref"] in ("J_PWR1", "U_SEED1") or p["ref"].startswith("U") else anchor_of(p)
        if p["ref"] == "J_PWR1":
            anchor = (18, 66)
            try:                                        # the connector body must not sit on front-side leads either
                x, y, rot, b = find(p, anchor, (0, 90, 180, 270), pad_only=True, body_clear=True)
            except RuntimeError:
                x, y, rot, b = find(p, anchor, (0, 90, 180, 270), pad_only=True)
        elif p["ref"] == "U_SEED1":
            x, y, rot, b = find(p, anchor, (0, 90, 180, 270), pad_only=True, step=1.0)
        else:
            x, y, rot, b = find(p, anchor, (0, 90))
        if p["ref"] == "U_SEED1":
            place_seed(p, x, y, rot)
            box3, _ = geometry("Daisy-Boards:DAISY_SEED2_DFM_3D", True, rot)     # the module outline is the keep-out for the other parts
            b = (min(b[0], x + box3[0]), min(b[1], y + box3[1]), max(b[2], x + box3[2]), max(b[3], y + box3[3]))
        else:
            make(p, x, y, rot, True)
        pos[p["ref"]] = (x, y)
        bot_obst.add(b)
        box, pads = geometry(p["fp"], True, rot)
        for q in pads:
            if q[4]:
                tht_obst.add(infl(shift(q[:4], x, y), 0.5))
        report.append((p["ref"], round(x, 1), round(y, 1), rot))
    pcbnew.SaveBoard(str(out), board)
    return report


if __name__ == "__main__":
    rep = build(sys.argv[1])
    for r in rep[:6] + rep[-3:]:
        print(r)
    print("placed", len(rep), "bottom parts; board saved")
