"""Senario Looper/MultiFX: the design as data (parts, nets, floorplan).

Everything the schematic and the PCB need comes from here:
  * `PARTS`   every part with its symbol, footprint, value and pin -> net map
  * `FLOOR`   fixed positions of the hand-soldered controls (top side)
  * `BOARD`   outline

Circuits are taken from Electrosmith's references (see docs/design-notes.md):
  Daisy Patch Rev8 (PCM3060 external codec, audio front ends), Seed2 DFM datasheet (codec I/O, Figures 1.3 and 1.5),
  Seed3 Eurorack Dev Kit Rev3 (power input, CV in/out, gate in, MIDI, 4051 pot mux) and the Tanghim audit
  (PCA9685 open drain LED rail, MIDI 3.3 V resistors).
"""
from collections import OrderedDict

# ---------------------------------------------------------------- footprints
FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_R1210 = "Resistor_SMD:R_1210_3225Metric"
FP_R1206 = "Resistor_SMD:R_1206_3216Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_CP = "Capacitor_SMD:CP_Elec_6.3x7.7"
FP_D = "Diode_SMD:D_SOD-323F"
FP_FB = "Inductor_SMD:L_0603_1608Metric"
FP_SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
FP_SOIC16 = "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"
FP_SOT23_5 = "Package_TO_SOT_SMD:SOT-23-5"
FP_SMDIP6 = "Package_DIP:SMDIP-6_W9.53mm"
FP_LED3 = "LED_THT:LED_D3.0mm"

# LCSC numbers (checked at JLCPCB in the Tanghim audit unless marked "?")
LCSC = {
    ("R", "0R"): "C21189", ("R", "10R"): "C22859", ("R", "33R"): "C23140", ("R", "100R"): "C22775",
    ("R", "220R"): "C22962", ("R", "330R"): "C23138", ("R", "470R"): "C23179", ("R", "1K"): "C21190",
    ("R", "4.7K"): "C23162", ("R", "10K"): "C25804", ("R", "15K"): "C22809", ("R", "33K"): "C4216",
    ("R", "47K"): "C25819", ("R", "62K"): "C23221", ("R", "100K"): "C25803", ("R", "120K"): "C25808",
    ("R", "1M"): "C22935", ("R", "3R3"): "C17945", ("R", "820R"): "C23253", ("R", "22K"): "C31850",
    ("C", "100nF"): "C14663", ("C", "10nF"): "C57112", ("C", "1nF"): "C1588", ("C", "330pF"): "C1664",
    ("C", "47pF"): "?", ("C", "1uF"): "C15849", ("C", "10uF"): "C15850",
    ("C", "100uF"): "C48971042",
    ("U", "MCP6004"): "?", ("U", "TL074"): "?", ("U", "PCM3060"): "?",
    ("U", "PCA9685"): "C92206", ("U", "74HC4051"): "?", ("U", "MCP23017"): "?",
    ("U", "LD1117S50"): "C71124", ("U", "74AHCT1G125"): "C7484", ("U", "H11L1"): "C274632",
    ("U", "MMBT3904"): "C20526", ("U", "LM4040-10"): "?",
}

# jack counts (the 108 mm board height leaves room for 16 jacks: see docs/design-notes.md)
N_CVIN, N_GIN, N_GOUT = 2, 1, 1

PARTS = []
_cnt = {}
_ctx = {"sheet": None, "block": None}


class blk:
    """Context manager: parts created inside belong to a schematic sheet and a PCB placement block."""

    def __init__(self, sheet, block):
        self.new = {"sheet": sheet, "block": block}

    def __enter__(self):
        self.old = dict(_ctx)
        _ctx.update(self.new)

    def __exit__(self, *a):
        _ctx.update(self.old)


def ref(prefix):
    _cnt[prefix] = _cnt.get(prefix, 0) + 1
    return f"{prefix}{_cnt[prefix]}"


def part(prefix, sym, fp, value, pins, side="B", padmap=None, lcsc=None, desc="", ref_=None, board_fp=None, **props):
    p = dict(ref=ref_ or ref(prefix), sym=sym, fp=fp, board_fp=board_fp, value=value, pins=dict(pins), side=side,
             padmap=padmap or {}, sheet=_ctx["sheet"], block=_ctx["block"], props=props, desc=desc)
    if lcsc:
        p["props"]["LCSC"] = lcsc
    PARTS.append(p)
    return p


def R(value, a, b, fp=FP_R, **kw):
    return part("R", "Device:R", fp, value, {"1": a, "2": b}, lcsc=LCSC.get(("R", value)), **kw)


def C(value, a, b, fp=FP_C, **kw):
    return part("C", "Device:C", fp, value, {"1": a, "2": b}, lcsc=LCSC.get(("C", value)), **kw)


def CP(value, a, b, fp=FP_CP, **kw):
    return part("C", "Device:C_Polarized", fp, value, {"1": a, "2": b}, lcsc=LCSC.get(("C", value)), **kw)


def D(value, k, a, **kw):
    return part("D", "Device:D_Schottky", FP_D, value, {"K": k, "A": a}, **kw)


def bypass(net, n=1, value="100nF", gnd="GND"):
    for _ in range(n):
        C(value, net, gnd)


# ------------------------------------------------------------------- jacks
J_MONO = "4ms_Jack:3.5mm_Mono_Switched"
FP_JMONO = "4ms_Jack:EighthInch_PJ398SM"


def jack(name, sig, sw="GND", label=None):
    """Thonkiconn mono jack. SIG = tip, SHEILD = sleeve, SW = tip-normalling switch contact. Ref J_<name>, value = label."""
    pins = {"1": sig, "2": "GND"}
    if sw:
        pins["3"] = sw
    return part("J", J_MONO, FP_JMONO, label or name, pins, side="T", ref_="J_" + name, block="jacks")


# ================================================================== POWER
with blk("Power", "power"):
    part("J", "4ms_Connector:Eurorack_Power_10pin_Shrouded", "4ms_Connector:Pins_2x05_2.54mm_TH_EurorackPower_Shrouded",
         "Eurorack power 10-pin", {"1": "-12V_IN", "2": "-12V_IN", "3": "GND", "4": "GND", "5": "GND", "6": "GND",
                                   "7": "GND", "8": "GND", "9": "+12V_IN", "10": "+12V_IN"}, side="B", ref_="J_PWR1")
    # reverse protection + filtering, as the Seed3 Eurorack Dev Kit
    part("FB", "Device:FerriteBead", FP_FB, "FB 0603", {"1": "+12V_IN", "2": "+12V_FB"})
    part("FB", "Device:FerriteBead", FP_FB, "FB 0603", {"1": "-12V_IN", "2": "-12V_FB"})
    D("NSR1020MW2T3G", "+12V", "+12V_FB")           # series Schottky: anode on the connector side
    D("NSR1020MW2T3G", "-12V_FB", "-12V")           # series Schottky on the negative rail (cathode to the connector)
    for rail in ("+12V", "-12V"):
        bypass(rail, 1, "100nF")
        C("10uF", rail, "GND", fp=FP_C0805)
        CP("100uF", rail if rail == "+12V" else "GND", "GND" if rail == "+12V" else rail)
    # Seed supply: 2 x 3R3 + 2 x 100 uF (Dev Kit)
    R("3R3", "+12V", "DSY_VIN_A", fp=FP_R1206)
    R("3R3", "DSY_VIN_A", "DSY_VIN", fp=FP_R1206)
    CP("100uF", "DSY_VIN_A", "GND")
    CP("100uF", "DSY_VIN", "GND")
    # +5 V for the PCM3060 analog supply, the LEDs and the gate-out buffers
    part("U", "Regulator_Linear:LD1117S50TR_SOT223", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", "LD1117S50",
         {"VI": "+12V", "VO": "+5V", "GND": "GND"}, lcsc=LCSC[("U", "LD1117S50")], block="power")
    C("10uF", "+12V", "GND", fp=FP_C0805)
    C("10uF", "+5V", "GND", fp=FP_C0805)
    bypass("+5V", 2)
    CP("100uF", "+5V", "GND")
    # -10 V reference for the CV inputs
    R("2K", "-12V", "-10V_REF")
    part("U", "Reference_Voltage:LM4040DBZ-10", FP_SOT23, "LM4040DBZ-10", {"K": "GND", "A": "-10V_REF", "NC": None})
    bypass("-10V_REF", 1)
    # bypass for the 3.3 V rails
    bypass("+3V3", 2)
    C("10uF", "+3V3", "GND", fp=FP_C0805)
    bypass("+3V3A", 1)
    C("10uF", "+3V3A", "GND", fp=FP_C0805)

# ================================================================== DAISY SEED2 DFM
SEED_PINS = {
    "D0": "OLED_RES", "D1": "GATE_IN_1", "D2": None, "D3": "GATE_OUT_1", "D4": None,
    "D5": "I2C_INT", "D6": "LED_OE", "D7": "OLED_CS", "D8": "OLED_SCK", "D9": "OLED_DC", "D10": "OLED_MOSI",
    "D11": "I2C_SCL", "D12": "I2C_SDA", "D13": "MIDI_TX", "D14": "MIDI_RX",
    "D15": "POT_MUX", "D16": None, "D17": "CV_IN_1_ADC", "D18": "CV_IN_2_ADC", "D19": None,
    "D20": None, "D21": "MUX_A", "D22": "CV_OUT_2_DAC", "D23": "CV_OUT_1_DAC",
    "D24": "SAI2_MCLK", "D25": "SAI2_SD_B", "D26": "SAI2_SD_A", "D27": "SAI2_FS", "D28": "SAI2_SCK",
    "D29": None, "D30": None, "D31": "MUX_B", "D32": "MUX_C",
    "VIN": "DSY_VIN", "3V3_D": "+3V3", "3V3_A": "+3V3A", "GND": "GND",
    "AUDIO_IN_1": "SEED_IN_L", "AUDIO_IN_2": "SEED_IN_R", "AUDIO_VCOM": "VCOM_SEED",
    "AUDIO_OUT_1+": "SEED_OUT_L+", "AUDIO_OUT_1-": "SEED_OUT_L-",
    "AUDIO_OUT_2+": "SEED_OUT_R+", "AUDIO_OUT_2-": "SEED_OUT_R-",
}
# The Seed module is not a board footprint: it plugs into five 2 x 5 1.27 mm female SMD sockets (Boomele 1.27-2*5PLTM, LCSC C59983,
# the part already sourced for Tanghim). The symbol stays the full 50-pin Seed (nets), the sockets carry the same nets pin by pin, and the
# board gets the pad-less 3D module footprint on top of them. seed_sockets.json says which Seed pad each socket pin touches.
import json as _json
from pathlib import Path as _Path
from kicad_sexp import load_symbol_lib as _lsl, symbol_pins as _sp
SEED_SOCKETS = _json.loads((_Path(__file__).parent / "seed_sockets.json").read_text())
_seed_sym = _lsl(_Path(__file__).resolve().parents[3] / "KicadLibs" / "symbols" / "Daisy-Boards.kicad_sym")["Daisy_Seed2_DFM"]
_pad_net = {}
for _p in _sp(_seed_sym):
    if _p["name"] in SEED_PINS:
        _pad_net[_p["number"]] = SEED_PINS[_p["name"]]
FP_SEED_SOCKET = "Daisy_Seed_Misc:PinSocket_2x05_P1.27mm_SMD_Boomele_C59983"
with blk("Daisy", "seed"):
    part("U", "Daisy-Boards:Daisy_Seed2_DFM", "", "Daisy Seed2 DFM", SEED_PINS, side="B", ref_="U_SEED1",
         board_fp="Daisy-Boards:DAISY_SEED2_DFM", desc="Daisy Seed2 DFM module (Electrosmith, bought), plugs into the five sockets J_SEED_A..E, back side")
    C("100nF", "VCOM_SEED", "GND")
with blk("Daisy", "seedsock"):
    for _letter in "ABCDE":
        part("J", "Connector_Generic:Conn_02x05_Odd_Even", FP_SEED_SOCKET, "1.27-2*5PLTM",
             {n: _pad_net.get(pad) for n, pad in SEED_SOCKETS[_letter]["map"].items()},
             side="B", ref_=f"J_SEED_{_letter}", lcsc="C59983", desc=f"socket for the Seed bank {_letter}")

# ================================================================== AUDIO (Seed codec: Seed2 DFM Fig. 1.3 in / Fig. 1.5 out)
with blk("Audio", "audio_seed"):
    # inputs: 10u coupling, 66K5, TL074 inverting, 15K || 220p, VCOM reference
    jack("AIN1", "AIN1_TIP")
    jack("AIN2", "AIN2_TIP")
    jack("AOUT1", "AOUT_ML_TIP", sw=None, label="OUT MAIN L")
    jack("AOUT2", "AOUT_MR_TIP", sw=None, label="OUT MAIN R")
    for ch, (tip, inn, outn) in {"L": ("AIN1_TIP", "SEED_IN_L", "SEED_AIN_L_NODE"),
                                  "R": ("AIN2_TIP", "SEED_IN_R", "SEED_AIN_R_NODE")}.items():
        pass
    # op-amp stages: U_A1 TL074: unit1 = in L, unit2 = in R, unit3 = out L, unit4 = out R
    for tip, node, inv, out, final, u in (("AIN1_TIP", "SIN_L_C", "SIN_L_INV", "SIN_L_OUT", "SEED_IN_L", 1),
                                           ("AIN2_TIP", "SIN_R_C", "SIN_R_INV", "SIN_R_OUT", "SEED_IN_R", 2)):
        C("10uF", tip, node, fp=FP_C0805)
        R("66K5", node, inv)
        R("15K", inv, out)
        C("220pF", inv, out)
        R("1K", out, final)
    # outputs (AC coupled, Fig. 1.5): L+ 18K -> 66K5 -> inv, 39K || 18p feedback, L- 18K -> 66K5 -> +, 39K to VCOM
    for ch, (p, n, tipnet) in {"L": ("SEED_OUT_L+", "SEED_OUT_L-", "AOUT_ML_TIP"),
                                "R": ("SEED_OUT_R+", "SEED_OUT_R-", "AOUT_MR_TIP")}.items():
        a, b, inv, nin, o, c = (f"SO{ch}_A", f"SO{ch}_B", f"SO{ch}_INV", f"SO{ch}_NI", f"SO{ch}_OUT", f"SO{ch}_AC")
        R("18K", p, a)
        R("66K5", a, inv)
        C("100pF", a, "GND")
        R("39K", inv, o)
        C("18pF", inv, o)
        R("18K", n, b)
        R("66K5", b, nin)
        C("18pF", b, "GND")
        R("39K", nin, "VCOM_SEED")
        C("10uF", o, c, fp=FP_C0805)
        R("100R", c, tipnet)
        R("10K", c, "GND")
    part("U", "Amplifier_Operational:TL074", FP_SOIC14, "TL074", {
        "3": "VCOM_SEED", "2": "SIN_L_INV", "1": "SIN_L_OUT",
        "5": "VCOM_SEED", "6": "SIN_R_INV", "7": "SIN_R_OUT",
        "10": "SOL_NI", "9": "SOL_INV", "8": "SOL_OUT",
        "12": "SOR_NI", "13": "SOR_INV", "14": "SOR_OUT", "4": "+12V", "11": "-12V"}, lcsc="?", ref_="U_A1")
    bypass("+12V", 1)
    bypass("-12V", 1)

# ================================================================== AUDIO (external PCM3060, Daisy Patch Rev8)
with blk("Audio", "audio_ext"):
    jack("AIN3", "AIN3_TIP")
    jack("AIN4", "AIN4_TIP")
    jack("AOUT3", "AOUT_SL_TIP", sw=None, label="OUT SEND L")
    jack("AOUT4", "AOUT_SR_TIP", sw=None, label="OUT SEND R")
    # inputs: 100K -> TL074 inverting (10K + 510R || 47p) -> 10u -> 100K -> TL074 inverting (100K || 47p) referenced to VCOM -> 1K
    for k, (tip, final) in enumerate((("AIN3_TIP", "EXT_IN_L"), ("AIN4_TIP", "EXT_IN_R"))):
        n = f"E{k}"
        R("100K", tip, f"{n}_INV1")
        R("10K", f"{n}_INV1", f"{n}_MID1")
        R("510R", f"{n}_MID1", f"{n}_OUT1")
        C("47pF", f"{n}_INV1", f"{n}_OUT1")
        C("10uF", f"{n}_OUT1", f"{n}_AC", fp=FP_C0805)
        R("100K", f"{n}_AC", f"{n}_INV2")
        R("100K", f"{n}_INV2", f"{n}_OUT2")
        C("47pF", f"{n}_INV2", f"{n}_OUT2")
        R("1K", f"{n}_OUT2", final)
    part("U", "Amplifier_Operational:TL074", FP_SOIC14, "TL074", {
        "3": "GND", "2": "E0_INV1", "1": "E0_OUT1", "12": "VCOM_EXT", "13": "E0_INV2", "14": "E0_OUT2",
        "5": "GND", "6": "E1_INV1", "7": "E1_OUT1", "10": "VCOM_EXT", "9": "E1_INV2", "8": "E1_OUT2",
        "4": "+12V", "11": "-12V"}, lcsc="?", ref_="U_A2")
    bypass("+12V", 1)
    bypass("-12V", 1)
    # outputs: C 10u -> (15K || 220K) -> TL074 inverting (100K || 47p) -> 100K -> inverting (100K || 47p) -> 1K; 47K load
    for k, (src, tip) in enumerate((("EXT_OUT_L", "AOUT_SL_TIP"), ("EXT_OUT_R", "AOUT_SR_TIP"))):
        n = f"X{k}"
        C("10uF", src, f"{n}_AC", fp=FP_C0805)
        R("47K", f"{n}_AC", "GND")
        R("15K", f"{n}_AC", f"{n}_INV1")
        R("220K", f"{n}_AC", f"{n}_INV1")
        R("100K", f"{n}_INV1", f"{n}_OUT1")
        C("47pF", f"{n}_INV1", f"{n}_OUT1")
        R("100K", f"{n}_OUT1", f"{n}_INV2")
        R("100K", f"{n}_INV2", f"{n}_OUT2")
        C("47pF", f"{n}_INV2", f"{n}_OUT2")
        R("1K", f"{n}_OUT2", tip)
    part("U", "Amplifier_Operational:TL074", FP_SOIC14, "TL074", {
        "3": "GND", "2": "X0_INV1", "1": "X0_OUT1", "12": "GND", "13": "X0_INV2", "14": "X0_OUT2",
        "5": "GND", "6": "X1_INV1", "7": "X1_OUT1", "10": "GND", "9": "X1_INV2", "8": "X1_OUT2",
        "4": "+12V", "11": "-12V"}, lcsc="?", ref_="U_A3")
    bypass("+12V", 1)
    bypass("-12V", 1)
    # PCM3060: H/W mode, single-ended, slave, 24-bit left-justified, de-emphasis off
    part("U", "Audio:PCM3060", "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm", "PCM3060PW", {
        "28": "PCM_MODE", "1": "PCM_FMT", "2": "PCM_DEMP", "27": "PCM_IFMD", "15": "PCM_RST",
        "3": "SAI2_SD_B", "4": "SAI2_FS", "5": "SAI2_SCK", "6": "SAI2_MCLK",
        "9": "SAI2_MCLK", "10": "SAI2_SCK", "11": "SAI2_FS", "12": "SAI2_SD_A",
        "7": "+3V3", "8": "GND", "24": "+5V", "23": "GND", "22": "GND", "16": "GND", "21": "VCOM_EXT",
        "25": "EXT_IN_L", "26": "EXT_IN_R", "20": "EXT_OUT_L", "18": "EXT_OUT_R",
        "19": None, "17": None, "13": None, "14": None}, lcsc="?", ref_="U_CODEC1")
    R("220K", "+3V3", "PCM_MODE")        # H/W mode, single-ended outputs
    R("10K", "+3V3", "PCM_FMT")          # 24-bit left-justified
    R("10K", "PCM_DEMP", "GND")          # de-emphasis off
    R("10K", "PCM_IFMD", "GND")          # slave: the Seed masters the clocks
    R("10K", "+3V3", "PCM_RST")
    C("1uF", "PCM_RST", "GND")
    C("2.2uF", "VCOM_EXT", "GND", fp=FP_C0805)
    bypass("VCOM_EXT", 1)
    bypass("+3V3", 1)
    C("10uF", "+3V3", "GND", fp=FP_C0805)
    bypass("+5V", 1)
    C("10uF", "+5V", "GND", fp=FP_C0805)

# ================================================================== CV / GATE
with blk("CV_Gate", "cvgate"):
    # CV in x4 (Dev Kit): 100K in, 200K from -10V_REF, 33K || 1nF feedback, MCP6004 on +3V3A: +/-5 V -> 3.3 .. 0 V
    for i in range(1, N_CVIN + 1):
        jack(f"CVIN{i}", f"CVIN{i}_TIP")
        R("100K", f"CVIN{i}_TIP", f"CVIN{i}_INV")
        R("200K", "-10V_REF", f"CVIN{i}_INV")
        R("33K", f"CVIN{i}_INV", f"CV_IN_{i}_ADC")
        C("1nF", f"CVIN{i}_INV", f"CV_IN_{i}_ADC")
    part("U", "Amplifier_Operational:MCP6004", FP_SOIC14, "MCP6004", {
        "3": "GND", "2": "CVIN1_INV", "1": "CV_IN_1_ADC",
        "5": "GND", "6": "CVIN2_INV", "7": "CV_IN_2_ADC",
        "4": "+3V3A", "11": "GND"}, lcsc="?", ref_="U_CVI1")
    bypass("+3V3A", 1)
    # CV out x2 (Dev Kit): DAC -> TL074 non-inverting, 120K / 62K (x1.52): 0 .. 5 V, 100R
    for i in (1, 2):
        jack(f"CVOUT{i}", f"CVOUT{i}_TIP", sw=None)
        R("120K", f"CVO{i}_INV", "GND")
        R("62K", f"CVO{i}_INV", f"CVO{i}_OUT")
        R("100R", f"CVO{i}_OUT", f"CVOUT{i}_TIP")
        R("1M", f"CV_OUT_{i}_DAC", "GND")           # keep the DAC pin defined while the bootloader runs
    part("U", "Amplifier_Operational:TL074", FP_SOIC14, "TL074", {
        "3": "CV_OUT_1_DAC", "2": "CVO1_INV", "1": "CVO1_OUT",
        "5": "CV_OUT_2_DAC", "6": "CVO2_INV", "7": "CVO2_OUT", "4": "+12V", "11": "-12V"}, lcsc="?", ref_="U_CVO1")
    bypass("+12V", 1)
    bypass("-12V", 1)
    # gate in x2 (Dev Kit): 100K, MMBT3904, 1M, 10K pull-up, 100R (inverted: a high gate reads 0)
    for i in range(1, N_GIN + 1):
        jack(f"GATEIN{i}", f"GATEIN{i}_TIP")
        R("100K", f"GATEIN{i}_TIP", f"GI{i}_B")
        R("1M", f"GI{i}_B", "GND")
        R("10K", "+3V3", f"GI{i}_C")
        R("100R", f"GI{i}_C", f"GATE_IN_{i}")
        part("Q", "Transistor_BJT:MMBT3904", FP_SOT23, "MMBT3904", {"B": f"GI{i}_B", "E": "GND", "C": f"GI{i}_C"},
             lcsc=LCSC[("U", "MMBT3904")])
    # gate out x2: 74AHCT1G125 on +5 V, 100K pull-down on the GPIO, 1K to the tip: 0 / 5 V
    for i in range(1, N_GOUT + 1):
        jack(f"GATEOUT{i}", f"GATEOUT{i}_TIP", sw=None)
        R("100K", f"GATE_OUT_{i}", "GND")
        part("U", "74xGxx:74AHCT1G125", FP_SOT23_5, "74AHCT1G125",
             {"1": "GND", "2": f"GATE_OUT_{i}", "3": "GND", "4": f"GATEOUT{i}_BUF", "5": "+5V"}, lcsc=LCSC[("U", "74AHCT1G125")])
        R("1K", f"GATEOUT{i}_BUF", f"GATEOUT{i}_TIP")
        bypass("+5V", 1)

# ================================================================== MIDI (TRS type A)
with blk("CV_Gate", "midi"):
    part("J", "Senario:Jack_TRS", "4ms_Jack:EighthInch_Stereo_PJ366ST", "MIDI IN",
         {"1": "MIDI_IN_TIP", "3": "MIDI_IN_RING", "2": "MIDI_IN_SH"}, side="T", ref_="J_MIDIIN1",
         desc="TRS type A: tip = sink (DIN 5), ring = source (DIN 4)")
    part("J", "Senario:Jack_TRS", "4ms_Jack:EighthInch_Stereo_PJ366ST", "MIDI OUT",
         {"1": "MIDI_OUT_TIP", "3": "MIDI_OUT_RING", "2": "GND"}, side="T", ref_="J_MIDIOUT1")
    C("100nF", "MIDI_IN_SH", "GND")
    R("220R", "MIDI_IN_RING", "MIDI_OPTO_A")
    D("1N5817WS", "MIDI_OPTO_A", "MIDI_IN_TIP")      # reverse protection across the LED
    part("U", "Isolator:H11L1", FP_SMDIP6, "H11L1",
         {"1": "MIDI_OPTO_A", "2": "MIDI_IN_TIP", "3": None, "4": "MIDI_RX", "5": "GND", "6": "+3V3"},
         lcsc=LCSC[("U", "H11L1")])
    R("470R", "+3V3", "MIDI_RX")
    bypass("+3V3", 1)
    R("10R", "MIDI_TX", "MIDI_OUT_TIP")
    R("33R", "+3V3", "MIDI_OUT_RING", fp=FP_R1210)    # CA-033: 33 R / 0.5 W

# ================================================================== CONTROLS: I/O expanders, LED drivers, mux
with blk("Controls", "io"):
    for k, (addr, sigs) in enumerate(((0x20, {}), (0x21, {}))):
        pass
    ENC = [(f"ENC{i}_A", f"ENC{i}_B", f"ENC{i}_SW") for i in range(1, 5)]
    BTN = [f"BTN{i}" for i in range(1, 7)]
    MX = [f"MX{i}" for i in range(1, 9)]
    io1 = [s for e in ENC for s in e] + BTN[:4]               # 16
    io2 = BTN[4:] + MX                                          # 10 (+ 6 spare)
    for u, (ref_, a, sigs) in enumerate((("U_IO1", (0, 0, 0), io1), ("U_IO2", (1, 0, 0), io2))):
        pins = {"V_{DD}": "+3V3", "V_{SS}": "GND", "SCK": "I2C_SCL", "SDA": "I2C_SDA",
                "A0": "+3V3" if a[0] else "GND", "A1": "GND", "A2": "GND", "~{RESET}": "+3V3",
                "INTA": "I2C_INT", "INTB": "I2C_INT"}
        gpio = [f"GPA{i}" for i in range(8)] + [f"GPB{i}" for i in range(8)]
        for g, s in zip(gpio, sigs + [None] * 16):
            pins[g] = s
        part("U", "Interface_Expansion:MCP23017x-x-SS", "Package_SO:SSOP-28_5.3x10.2mm_P0.65mm", "MCP23017",
             pins, lcsc="?", ref_=ref_)
        bypass("+3V3", 1)
    R("10K", "+3V3", "I2C_INT")
    R("4.7K", "+3V3", "I2C_SCL")
    R("4.7K", "+3V3", "I2C_SDA")
    # LED drivers: PCA9685 open drain, LEDs on +5V through 330R. 0x40: keys, buttons, PTL LEDs (16). 0x41: the 4 encoder RGB LEDs (12 of 16)
    LED_CH = {}
    names = [f"LED_MX{i}" for i in range(1, 9)] + [f"LED_BTN{i}" for i in range(1, 7)] + ["LED_PTL1", "LED_PTL2"]
    names += [f"LED_ENC{i}_{c}" for i in range(1, 5) for c in "RGB"]         # 12 channels on the second chip
    for u, (ref_, a0) in enumerate((("U_LED1", "GND"), ("U_LED2", "+3V3"))):
        pins = {"A0": a0, "A1": "GND", "A2": "GND", "A3": "GND", "A4": "GND", "A5": "GND", "VSS": "GND",
                "VDD": "+3V3", "~{OE}": "LED_OE", "EXTCLK": "GND", "SCL": "I2C_SCL", "SDA": "I2C_SDA"}
        for ch in range(16):
            idx = u * 16 + ch
            pins[f"LED{ch}"] = (names[idx] + "_K") if idx < len(names) else None
        part("U", "Driver_LED:PCA9685PW", "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm", "PCA9685PW", pins,
             lcsc=LCSC[("U", "PCA9685")], ref_=ref_)
        bypass("+3V3", 1)
        C("10uF", "+3V3", "GND", fp=FP_C0805)
    R("10K", "+3V3", "LED_OE")                     # LEDs off until the firmware enables them
    # panel analog: 74HC4051 on +3V3A. 0 PTL1 | 1 PTL2 | 2 slider | 3 POT1 | 4 POT2
    part("U", "74xx:74HC4051", FP_SOIC16, "74HC4051",
         {"A0": "WIP_PTL1", "A1": "WIP_PTL2", "A2": "WIP_SL", "A3": "WIP_POT1", "A4": "WIP_POT2",
          "A5": None, "A6": None, "A7": None, "A": "POT_MUX", "S0": "MUX_A", "S1": "MUX_B", "S2": "MUX_C",
          "~{E}": "GND", "VEE": "GND", "GND": "GND", "VCC": "+3V3A"}, lcsc="?", ref_="U_MUX1")
    bypass("+3V3A", 1)
    C("10nF", "POT_MUX", "GND")

# ================================================================== OLED
with blk("Controls", "oled"):
    part("J", "Display_OLED:OLED_HS96L01W4S03", "Daisy_Seed_Misc:OLED_0.96in_SPI_Module_HS96L01W4S03", "HS96L01W4S03",
         {"GND": "GND", "VCC": "+3V3", "SCL": "OLED_SCK", "SDA": "OLED_MOSI", "RES": "OLED_RES", "DC": "OLED_DC", "CS": "OLED_CS"},
         side="T", ref_="J_OLED1", lcsc="C5139758")
    C("10uF", "+3V3", "GND", fp=FP_C0805)
    bypass("+3V3", 1)

# ================================================================== CONTROLS (front side, hand soldered)
SYM_PUSH_LED = "Senario:SW_Tact_LED_6pin"
with blk("Controls", "panel"):
    for i in range(1, 5):                      # illuminated encoders: Top-Up EC12PL RGB (SparkFun COM-15141), common anode on +5 V
        part("ENC", "Senario:Encoder_RGB_SW", "Daisy_Seed_Misc:ENC_RGB_TopUp_EC12PLRGB", "EC12PLRGBSDVBF RGB encoder",
             {"A": f"ENC{i}_A", "C": "GND", "B": f"ENC{i}_B", "S": "GND",
              "1": f"LED_ENC{i}_R_LK", "2": f"LED_ENC{i}_G_LK", "4": f"LED_ENC{i}_B_LK", "5": "+5V", "3": f"ENC{i}_SWP"},
             side="T", ref_=f"ENC{i}")
        R("330R", f"LED_ENC{i}_R_K", f"LED_ENC{i}_R_LK")        # PCA9685 sinks each colour
        R("220R", f"LED_ENC{i}_G_K", f"LED_ENC{i}_G_LK")
        R("220R", f"LED_ENC{i}_B_K", f"LED_ENC{i}_B_LK")
        # the push switch connects pin 3 to the common anode (+5 V): divide 5 V to 3.0 V for the 3.3 V expander, 25K pulls it low
        R("10K", f"ENC{i}_SWP", f"ENC{i}_SW")
        R("15K", f"ENC{i}_SW", "GND")
    for i in range(1, 9):                      # Cherry MX + red 3 mm LED in the switch window
        part("SW", "Switch:SW_Push", "Switch_Keyboard_Cherry_MX:SW_Cherry_MX_PCB_1.00u", "Cherry MX Red",
             {"1": f"MX{i}", "2": "GND"}, side="T", ref_=f"SW_MX{i}")
        part("LED", "Device:LED", FP_LED3, "LED red 3mm", {"K": f"LED_MX{i}_K", "A": f"LED_MX{i}_A"}, side="T", ref_=f"LED_MX{i}")
        R("330R", "+5V", f"LED_MX{i}_A")
    for i in range(1, 7):                      # push buttons with LED on top: Hroparts K6-6140A-02 (red). Only 1 and 2 are placed (flanking the slider)
        part("SW", SYM_PUSH_LED, "Daisy_Seed_Misc:SW_Tact_LED_Hroparts_K6-6140A_THT", "K6-6140A-02 (red LED)" if i <= 2 else "K6-6140A-03 (blue LED)",
             {"1": f"BTN{i}", "2": f"BTN{i}", "3": "GND", "4": "GND", "5": f"LED_BTN{i}_K", "6": f"LED_BTN{i}_A"},
             side="T", ref_=f"SW_BTN{i}")
        R("330R" if i <= 2 else "150R", "+5V", f"LED_BTN{i}_A")        # blue LED: Vf about 3.2 V, 150R gives about 10 mA from 5 V (datasheet gives no LED data: check)
    for i in (1, 2):                           # Bourns PTL30 slide pots with LED
        part("PTL", "Bourns_PTL:PTL20", "Bourns_PTL:Bourns_PTL20_Slide_LED", "PTL20-15R 10K",
             {"1": "GND", "2": f"WIP_PTL{i}", "3": "+3V3A", "E": f"LED_PTL{i}_K", "B": f"LED_PTL{i}_A", "L": None},
             side="T", ref_=f"PTL{i}")
        R("330R", "+5V", f"LED_PTL{i}_A")
    part("SL", "4ms_Potentiometer:Pot_Slider_60mm_10k", "Daisy_Seed_Misc:ALPS-RS6011_60mm_Panel", "Alps RS6011 60mm 10K",
         {"1": "GND", "2": "WIP_SL", "3": "+3V3A", "4": None, "5": None, "6": None, "7": None, "8": None}, side="T", ref_="SL1")
    for i in (1, 2):
        part("VR", "4ms_Potentiometer:9mm_NoDet_10k_DShaft", "4ms_Potentiometer:Pot_9mm_DShaft", "10K linear 9mm",
             {"1": "GND", "2": f"WIP_POT{i}", "3": "+3V3A", "4": "GND", "5": "GND"}, side="T", ref_=f"VR{i}")

# mounting holes (M2.5, in the corners)
with blk("Power", "holes"):
    for i in range(1, 5):
        part("H", "Mechanical:MountingHole", "MountingHole:MountingHole_2.7mm_M2.5", "M2.5", {}, side="T", ref_=f"H{i}")

# Parts left out of the PCB placement for now (the schematic keeps them). Set to () to bring them back.
PCB_HIDE_REFS = ("VR",)                                                  # the two pots (buttons 1, 2 flank the slider, 3-6 are under it)
PCB_HIDE_NETS = ()                                                       # (nothing else hidden)


def pcb_hidden(p):
    """True for parts that are in the schematic but not (yet) on the board or in the BOM."""
    if any(p["ref"].startswith(x) for x in PCB_HIDE_REFS):
        return True
    return p["ref"].startswith("R") and any(str(n).startswith(PCB_HIDE_NETS) for n in p["pins"].values() if n)


# ================================================================== FLOORPLAN (front side, mm, origin = board top-left)
# 24HP: panel 121.92 nominal (about 121.55 real). Board 120 x 108: height = 128.5 panel - 2 x 10 mm rail clearance - 0.5
# (community rule: board <= 108..110 mm, parts 10 mm clear of the top and bottom edges of the panel; see docs/design-notes.md)
BOARD = dict(w=120.0, h=108.0)
FLOOR = OrderedDict()
JX = [6.5 + 10.8 * i for i in range(4)] + [79.7 + 10.8 * i for i in range(4)]   # inputs | OLED | outputs
JY = [7.5, 22.5]
_grid = [  # (row, col): jack. Left block = inputs, OLED in the middle, right block = outputs; two jacks per column
    (0, 0, "AIN1"), (1, 0, "AIN2"),            # audio in 1, 2 (Seed codec)
    (0, 1, "AIN3"), (1, 1, "AIN4"),            # audio in 3, 4 (PCM3060)
    (0, 2, "CVIN1"), (1, 2, "CVIN2"),
    (0, 3, "GATEIN1"), (1, 3, "MIDIIN1"),
    (0, 4, "AOUT1"), (1, 4, "AOUT2"),          # out main L, R
    (0, 5, "AOUT3"), (1, 5, "AOUT4"),          # out send L, R
    (0, 6, "CVOUT1"), (1, 6, "CVOUT2"),
    (0, 7, "GATEOUT1"), (1, 7, "MIDIOUT1"),
]
for r_, c_, n in _grid:
    FLOOR["J_" + n] = (JX[c_], JY[r_], 90)
FLOOR["J_OLED1"] = (52.53, 2.82, 0)                   # module x 46.5 .. 73.8, y 1.5 .. 29.3, between the input and output jack blocks
KX = [60.0 - 28.575 + 19.05 * i for i in range(4)]
for i, x in enumerate(KX, 1):                         # each encoder on the axis of the key column below it
    FLOOR[f"ENC{i}"] = (x, 39.5, 0)
KY = [56.5, 75.55]
for n in range(8):
    FLOOR[f"SW_MX{n + 1}"] = (KX[n % 4], KY[n // 4], 180)                 # turned 180: the LED window faces up
    FLOOR[f"LED_MX{n + 1}"] = (KX[n % 4] - 1.27, KY[n // 4] - 5.08, 0)    # footprint origin is pad 1: -1.27 centres the LED
FLOOR["PTL1"] = (9.0, 66.0, 90)                       # PTL20 left and right of the matrix
FLOOR["PTL2"] = (111.0, 66.0, 90)
for i, x in enumerate((40.5, 53.5, 66.5, 79.5)):
    FLOOR[f"SW_BTN{i + 3}"] = (x, 102.5, 0)                # row of 4 under the slider
FLOOR["VR1"] = (21.0, 91.5, 0)
FLOOR["VR2"] = (99.0, 91.5, 0)
FLOOR["SL1"] = (60.0, 92.15, 0)                       # Alps RS6011 60 mm: body top 3 mm below the lowest keycap edge (84.55), body 9.2 mm tall
FLOOR["SW_BTN1"] = (15.0, 92.15, 0)
FLOOR["SW_BTN2"] = (105.0, 92.15, 0)
FLOOR["H1"], FLOOR["H2"], FLOOR["H3"], FLOOR["H4"] = [(x, y, 0) for x, y in ((2.0, 38.0), (118.0, 38.0), (2.3, 106.2), (117.7, 106.2))]

# bottom side anchors (where the SMD blocks should sit: behind the controls they serve)
ANCHOR = {
    "power": (18, 66), "seed": (60, 70), "audio_seed": (25, 20), "audio_ext": (60, 20), "cvgate": (80, 20),
    "midi": (88, 28), "io": (60, 60), "oled": (60, 20), "panel": (60, 80), "holes": (60, 50),
}


# ================================================================== 3D MODELS (project-level fixes, applied when the PCB is generated)
# The 4ms and keyswitch footprints point to their PCM-package folders (${KICAD10_3RD_PARTY}/...); the same files are in KicadLibs/3dmodels.
MODEL_PATH_REMAP = {
    "${KICAD10_3RD_PARTY}/3dmodels/com_github_4ms_4ms-kicad-lib/": "${KICADLIBS}/3dmodels/",
    "${KICAD6_3RD_PARTY}/3dmodels/com_github_perigoso_keyswitch-kicad-library/3d-library.3dshapes/": "${KICADLIBS}/3dmodels/3d-library.3dshapes/",
}
# footprints without a model, or whose model needs another transform: {fpid: (file, offset xyz mm, rotate xyz deg, scale)}
MODEL_OVERRIDE = {
    # placeholders (models/*.wrl, written by gen_placeholder_models.py) for parts with no public model
    "Bourns_PTL:Bourns_PTL20_Slide_LED": ("${KIPRJMOD}/models/PTL20_placeholder.wrl", (0, 0, 0), (0, 0, 0), (0.3937, 0.3937, 0.3937)),
    "Daisy_Seed_Misc:ALPS-RS6011_60mm_Panel": ("${KIPRJMOD}/models/Alps_RS6011_placeholder.wrl", (0, 0, 0), (0, 0, 0), (0.3937, 0.3937, 0.3937)),
    "Daisy_Seed_Misc:OLED_0.96in_SPI_Module_HS96L01W4S03": ("${KIPRJMOD}/models/OLED_HS96L01_placeholder.wrl", (0, 0, 0), (0, 0, 0), (0.3937, 0.3937, 0.3937)),
    "4ms_Jack:EighthInch_PJ398SM": ("${KICADLIBS}/3dmodels/Jack.3dshapes/WQP-PJ398SM.step", (0, 0, 0), (0, 0, -90), (1, 1, 1)),   # the Thonkiconn model, as the 4ms stereo footprint
    "Daisy_Seed_Misc:ENC_RGB_TopUp_EC12PLRGB": ("${KIPRJMOD}/models/Encoder_RGB_TopUp_placeholder.wrl", (0, 0, 0), (0, 0, 0), (0.3937, 0.3937, 0.3937)),
}
