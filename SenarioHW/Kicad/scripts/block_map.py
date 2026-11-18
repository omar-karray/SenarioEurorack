"""Back-side block map: SVG of the saved board (run from SenarioHW/Kicad with KiCad's Python): dashed = front blocks, filled = back SMD parts by block.
Usage: block_map.py out.svg"""
import pcbnew, re, collections, sys
mm=pcbnew.ToMM
b=pcbnew.LoadBoard("Senario.kicad_pcb")
fp={f.GetReference():f for f in b.GetFootprints()}
blocks={
 "slider":["SL1","SW_BTN1","SW_BTN2"],"matrix":[f"SW_MX{i}" for i in range(1,9)]+[f"LED_MX{i}" for i in range(1,9)],
 "left col":["PTL1","VR1","VR3","SW_BTN7"],"right col":["PTL2","VR2","VR4","SW_BTN8"],
 "button row":["SW_BTN3","SW_BTN4","SW_BTN5","SW_BTN6"],"encoders":["ENC1","ENC2","ENC3","ENC4"],
 "oled":["J_OLED1"],"usb":["J_USB1"],
 "jack I/O":[r for r in fp if r.startswith("J_") and r not in ("J_OLED1","J_USB1","J_SD1","J_PWR1") and not r.startswith("J_SEED")],
}
COL={"slider":"#e6194b","matrix":"#3cb44b","left col":"#4363d8","right col":"#f58231","button row":"#911eb4","encoders":"#008080","oled":"#9a6324","usb":"#800000","jack I/O":"#808000","shared":"#000000","power":"#e6beff","seed":"#aaaaaa","sd":"#fabed4","other":"#bbbbbb"}
ref2b={r:k for k,v in blocks.items() for r in v}
RAIL={"GND","+3V3","+3V3A","+5V","+12V","-12V","-10V_REF","","VCOM_SEED","+5V_USB","DSY_VIN"}
n2p=collections.defaultdict(set)
for r,f in fp.items():
    for p in f.Pads():
        n=p.GetNetname()
        if n and n not in RAIL: n2p[n].add(r)
SHARED={"U_IO1","U_IO2","U_LED1","U_LED2","U_MUX1"}
back=[r for r,f in fp.items() if f.GetLayerName()=="B.Cu"]
assign={}
for r in back:
    bl=set()
    for p in fp[r].Pads():
        n=p.GetNetname()
        if n and n not in RAIL:
            for q in n2p[n]:
                if q in ref2b: bl.add(ref2b[q])
    if len(bl)==1 and r not in SHARED: assign[r]=bl.pop()
ch=True
while ch:
    ch=False
    for r in back:
        if r in assign or r in SHARED: continue
        c=set()
        for p in fp[r].Pads():
            n=p.GetNetname()
            if n and n not in RAIL:
                for q in n2p[n]:
                    if q in assign: c.add(assign[q])
        if len(c)==1: assign[r]=c.pop(); ch=True
for r in SHARED: assign[r]="shared"
for r in back:
    if r in assign: continue
    if r.startswith("J_SEED") or r=="U_SEED1": assign[r]="seed"
    elif r=="J_SD1" or r in ("C21","C22","R4","R5","R6","R7","R8"): assign[r]="sd"
    elif re.match(r"(C[1-9]|C1[0-9]|D[12]|FB|R[123]$|U1$|U2$|J_PWR1)",r): assign[r]="power"
    else: assign[r]="other"
S=8.0
W,H=120,108
o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S+260}" height="{W*S+260}" viewBox="0 0 {W*S+260} {W*S+260}"><rect width="100%" height="100%" fill="white"/>',f'<rect x="0" y="0" width="{W*S}" height="{H*S}" fill="#f4f4f4" stroke="black"/>']
for k,v in blocks.items():
    xs=[];ys=[]
    for r in v:
        bb=fp[r].GetBoundingBox(False); xs+=[mm(bb.GetLeft()),mm(bb.GetRight())]; ys+=[mm(bb.GetTop()),mm(bb.GetBottom())]
    o.append(f'<rect x="{min(xs)*S}" y="{min(ys)*S}" width="{(max(xs)-min(xs))*S}" height="{(max(ys)-min(ys))*S}" fill="none" stroke="{COL[k]}" stroke-width="2" stroke-dasharray="8 5"/>')
    o.append(f'<text x="{min(xs)*S+4}" y="{min(ys)*S+14}" font-size="13" fill="{COL[k]}" font-family="Helvetica" font-weight="bold">{k}</text>')
# front THT pads on the back (obstacles)
for r,f in fp.items():
    if f.GetLayerName()=="F.Cu":
        for p in f.Pads():
            if p.HasHole():
                bb=p.GetBoundingBox(); o.append(f'<rect x="{mm(bb.GetLeft())*S}" y="{mm(bb.GetTop())*S}" width="{mm(bb.GetWidth())*S}" height="{mm(bb.GetHeight())*S}" fill="#ffd700" fill-opacity="0.6"/>')
for r in back:
    f=fp[r]; bb=f.GetBoundingBox(False); k=assign[r]
    op=0.35 if k in ("seed",) else 0.85
    o.append(f'<rect x="{mm(bb.GetLeft())*S}" y="{mm(bb.GetTop())*S}" width="{mm(bb.GetWidth())*S}" height="{mm(bb.GetHeight())*S}" fill="{COL[k]}" fill-opacity="{op}" stroke="black" stroke-width="0.5"/>')
    if f.GetBoundingBox(False).GetWidth()>pcbnew.FromMM(4.5): o.append(f'<text x="{mm(bb.GetLeft())*S+2}" y="{mm(bb.GetTop())*S+11}" font-size="10" font-family="Helvetica" fill="black">{r}</text>')
# legend
y=20
for k,c in COL.items():
    n=sum(1 for r in back if assign[r]==k)
    o.append(f'<rect x="{W*S+12}" y="{y-11}" width="14" height="14" fill="{c}"/><text x="{W*S+32}" y="{y}" font-size="13" font-family="Helvetica">{k} ({n})</text>'); y+=22
o.append('<text x="%d" y="%d" font-size="11" font-family="Helvetica" fill="#555">dashed = front block, filled = back SMD part</text>'%(W*S+12,y+10))
o.append('<text x="%d" y="%d" font-size="11" font-family="Helvetica" fill="#555">yellow = front through-hole pads</text>'%(W*S+12,y+26))
o.append("</svg>")
open(sys.argv[1],"w").write("\n".join(o))
