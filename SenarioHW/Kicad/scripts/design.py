"""Senario Looper/MultiFX: the design as data (parts, nets, floorplan). Version-beta platform: see docs/spec-beta.md (22 jacks, 10 Lakeview RGB buttons, 4 Bourns encoders, MX + SK6812, MCP4728 CV out).

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
FP_SOT23_6 = "Package_TO_SOT_SMD:SOT-23-6"
FP_SMDIP6 = "Package_DIP:SMDIP-6_W9.53mm"
FP_LED3 = "LED_THT:LED_D3.0mm"

# LCSC numbers (checked at JLCPCB in the Tanghim audit unless marked "?")
LCSC = {
    ("R", "0R"): "C21189", ("R", "10R"): "C22859", ("R", "33R"): "C23140", ("R", "100R"): "C22775",
    ("R", "220R"): "C22962", ("R", "330R"): "C23138", ("R", "470R"): "C23179", ("R", "1K"): "C21190",
    ("R", "4.7K"): "C23162", ("R", "10K"): "C25804", ("R", "15K"): "C22809", ("R", "33K"): "C4216",
    ("R", "47K"): "C25819", ("R", "5K1"): "C23186", ("R", "62K"): "C23221", ("R", "100K"): "C25803", ("R", "120K"): "C25808",
    ("R", "1M"): "C22935", ("R", "3R3"): "C17945", ("R", "820R"): "C23253", ("R", "22K"): "C31850",
    ("C", "100nF"): "C14663", ("C", "10nF"): "C57112", ("C", "1nF"): "C1588", ("C", "330pF"): "C1664",
    ("C", "47pF"): "?", ("C", "1uF"): "C15849", ("C", "10uF"): "C15850", ("C", "22uF"): "C45783",
    ("C", "100uF"): "C48971042",
    ("U", "MCP6004"): "?", ("U", "TL074"): "?", ("U", "PCM3060"): "?",
    ("U", "PCA9685"): "C92206", ("U", "AP63205"): "C2071056", ("U", "USBLC6"): "C7519", ("U", "74HC4051"): "?", ("U", "MCP23017"): "?",
    ("U", "LD1117S50"): "C71124", ("U", "74AHCT1G125"): "C7484", ("U", "H11L1"): "C274632",
    ("U", "MMBT3904"): "C20526", ("U", "LM4040-10"): "?", ("U", "MCP4728"): "C108207",
}

# ---------------------------------------------------------------- platform constants (docs/spec-beta.md)
N_CVIN = 4                                                                                  # CV in 1-4 (Dev Kit stage, MCP6004 quad)
GATES_IN = [("GATEIN1", "GATE_IN_1"), ("GATEIN2", "GATE_IN_2"), ("CLKIN", "CLOCK_IN")]      # (jack name, net)
GATES_OUT = [("GATEOUT1", "GATE_OUT_1"), ("GATEOUT2", "GATE_OUT_2"), ("CLKOUT", "CLOCK_OUT")]
N_BTN = 10                                                                                  # BTN1-6 control row, BTN7 / BTN8 beside the sliders (TL1), BTN9 / BTN10 at the Alps slider (TL16)
OLED_MODEL = "0.96"                                                                         # "0.96" (HS96L01W4S03, in use) or "1.3" (HS13L01W4S01): the schematic, footprint and faceplate window follow
# CV out stage (Dev Kit: DAC -> TL074 non-inverting, 0 .. 5 V). The MCP4728 runs from 3V3 with its internal 2.048 V reference at gain 1 (its I2C inputs need VIH = 0.7 x VDD, which 3.3 V
# does not meet at VDD = 5 V), so the stage needs a gain of 5 / 2.048 = 2.44: 1 + Rf / Rg = 1 + 68K / 47K = 2.447 -> 5.01 V. CHANGE THESE TWO when the stage is redefined (full +-10 V Eurorack).
CVO_RG, CVO_RF = "47K", "68K"

PARTS = []
_cnt = {}
_ctx = {"sheet": None, "block": None, "group": None}


class blk:
    """Context manager: parts created inside belong to a schematic sheet and a PCB placement block."""

    def __init__(self, sheet, block):
        self.new = {"sheet": sheet, "block": block}

    def __enter__(self):
        self.old = dict(_ctx)
        _ctx.update(self.new)

    def __exit__(self, *a):
        _ctx.update(self.old)


class grp:
    """Context manager: parts created inside one `with grp(name)` are drawn together on their own row of the schematic sheet (one channel, one button with its resistors ...)."""

    def __init__(self, name):
        self.new = {"group": name}

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
             padmap=padmap or {}, sheet=_ctx["sheet"], block=_ctx["block"], group=_ctx["group"], props=props, desc=desc)
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

with blk("Power", "seedpwr"):
    # Seed supply: 2 x 3R3 + 2 x 100 uF (Dev Kit); placed next to the Seed's socket A (the DSY_VIN pins), in the free space of the right column
    R("3R3", "+12V", "DSY_VIN_A", fp=FP_R1206)
    R("3R3", "DSY_VIN_A", "DSY_VIN", fp=FP_R1206)
    CP("100uF", "DSY_VIN_A", "GND")
    CP("100uF", "DSY_VIN", "GND")
with blk("Power", "power"):
    # analog +5 V: LD1117 + ferrite bead + a second 10 uF, as the "+5V ANALOG" section of the Daisy Patch. Only the PCM3060 analog supply and the gate-out buffers
    # (a few tens of mA): the LED current is on its own rail (+5V_LED, below).
    part("U", "Regulator_Linear:LD1117S50TR_SOT223", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", "LD1117S50",
         {"VI": "+12V", "VO": "+5V_LDO", "GND": "GND"}, lcsc=LCSC[("U", "LD1117S50")], block="power")
    C("10uF", "+12V", "GND", fp=FP_C0805)
    C("10uF", "+5V_LDO", "GND", fp=FP_C0805)
    part("FB", "Device:FerriteBead", FP_FB, "FB 0603", {"1": "+5V_LDO", "2": "+5V"})
    C("10uF", "+5V", "GND", fp=FP_C0805)
    bypass("+5V", 1)
    # LED +5 V: AP63205 step-down (12 V -> 5 V, 2 A, fixed 5 V), datasheet typical circuit: 10 uF in, 4.7 uH, 2 x 22 uF out, 100 nF bootstrap, EN to VIN, FB to the output.
    # It feeds only the LED anodes (up to about 0.3 A with every LED on), so the 12 V -> 5 V drop is not burnt in a linear regulator.
    with blk("Power", "ledpwr"):                 # its own block: IC, inductor and capacitors placed together (the switching node must stay short)
        part("U", "Regulator_Switching:AP63205WU", FP_SOT23_6, "AP63205WU-7",
             {"1": "+5V_LED", "2": "+12V", "3": "+12V", "4": "GND", "5": "BUCK_SW", "6": "BUCK_BST"}, lcsc=LCSC[("U", "AP63205")], ref_="U_BUCK1")
        C("10uF", "+12V", "GND", fp=FP_C0805)
        C("100nF", "BUCK_BST", "BUCK_SW")
        part("L", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", "4.7uH 2.9A YNR4030-4R7M", {"1": "BUCK_SW", "2": "+5V_LED"}, lcsc="C340391")
        C("22uF", "+5V_LED", "GND", fp=FP_C0805)
        C("22uF", "+5V_LED", "GND", fp=FP_C0805)
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
    "D0": "CLOCK_IN", "D1": "SDMMC_D3", "D2": "SDMMC_D2", "D3": "SDMMC_D1", "D4": "SDMMC_D0",       # D1-D6 are the SDMMC1 pins (4-bit, as the Dev Kit microSD slot)
    "D5": "SDMMC_CMD", "D6": "SDMMC_CK", "D7": "OLED_DC", "D8": "OLED_SCK", "D9": "LED_DATA", "D10": "OLED_MOSI",
    "D11": "I2C_SCL", "D12": "I2C_SDA", "D13": "MIDI_TX", "D14": "MIDI_RX",
    "D15": "POT_MUX", "D16": "CLOCK_OUT", "D17": "CV_IN_1_ADC", "D18": "CV_IN_2_ADC", "D19": "GATE_IN_1",
    "D20": "GATE_OUT_1", "D21": "CV_IN_3_ADC", "D22": "GATE_OUT_2", "D23": "I2C_INT",                 # D22 / D23 (the Seed DACs) are plain GPIO now: the CV outs are on the MCP4728
    "D24": "SAI2_MCLK", "D25": "SAI2_SD_B", "D26": "SAI2_SD_A", "D27": "SAI2_FS", "D28": "SAI2_SCK",
    "D29": "USB_OTG_HS_N", "D30": "USB_OTG_HS_P", "D31": "CV_IN_4_ADC", "D32": "GATE_IN_2",
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
# microSD slot, wired the way the Seed3 Eurorack Dev Kit does it (U7): 47K pull-ups to 3V3 on CMD and DAT0-3, none on CLK, card detect not used, VDD from 3V3 (Seed 3V3_D),
# shield to GND. The slot is the VERTICAL Yamaichi PJS008U-3000-0 on the front: the card goes up through a 13.6 x 3.1 slot in the panel.
with blk("USB_SD", "sd"):
    part("J", "4ms_Connector:microSDCon_Vert_TH_PJS008U-3000", "4ms_Connector_Card:CardSlot_MicroSD_YamaichiPJS008U-3000", "PJS008U-3000-0 microSD (vertical)",
         {"1": "SDMMC_D2", "2": "SDMMC_D3", "3": "SDMMC_CMD", "4": "+3V3", "5": "SDMMC_CK", "6": "GND", "7": "SDMMC_D0", "8": "SDMMC_D1", "9": "GND", "10": "GND"},
         side="T", ref_="J_SD1", desc="Yamaichi PJS008U-3000-0, vertical, 10 pads (9 / 10 = shell); Mouser, not LCSC")
    for n in ("SDMMC_CMD", "SDMMC_D0", "SDMMC_D1", "SDMMC_D2", "SDMMC_D3"):
        R("47K", "+3V3", n)
    C("10uF", "+3V3", "GND", fp=FP_C0805)
    bypass("+3V3", 1)

# USB-C: vertical Hroparts TYPE-C-31-D-14D (24P, 13.3 mm high: at the 10.0 panel plane its mouth is 1.7 mm above the 11.6 panel top; the 15C, 10.5, would be 1.1 below it; the -14 family has no locating holes), wired as the Seed3 Eurorack Dev Kit (U14, J7, R1, R2):
# VBUS on its own net +5V_USB (it does not power the module), CC1 / CC2 5K1 to GND, D+ / D- (both rows) through a USBLC6-2SC6 ESD array to the Seed USB HS pins D30 / D29,
# SBU not connected, shield and GND to GND.
with blk("USB_SD", "usb"):
    part("J", "Connector:USB_C_Receptacle", "OK_Connector:USB_C_Vertical_Hroparts_TYPE-C-31-D-14D_SMD", "TYPE-C-31-D-14D",
         {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "+5V_USB", "A9": "+5V_USB", "B4": "+5V_USB", "B9": "+5V_USB",
          "A5": "USB_CC1", "B5": "USB_CC2", "A6": "USB_IN_P", "B6": "USB_IN_P", "A7": "USB_IN_N", "B7": "USB_IN_N",
          "A8": None, "B8": None, "A2": None, "A3": None, "A10": None, "A11": None, "B2": None, "B3": None, "B10": None, "B11": None, "SH": "GND"},
         side="T", ref_="J_USB1", lcsc="C22464496")
    part("U", "Power_Protection:USBLC6-2SC6", FP_SOT23_6, "USBLC6-2SC6",
         {"1": "USB_IN_P", "2": "GND", "3": "USB_IN_N", "4": "USB_OTG_HS_N", "5": "+5V_USB", "6": "USB_OTG_HS_P"}, lcsc=LCSC[("U", "USBLC6")], ref_="U_USB1")
    R("5K1", "USB_CC1", "GND")
    R("5K1", "USB_CC2", "GND")

with blk("Daisy", "seedsock"):
    for _letter in "ABCDE":
        part("J", "Connector_Generic:Conn_02x05_Odd_Even", FP_SEED_SOCKET, "1.27-2*5PLTM",
             {n: _pad_net.get(pad) for n, pad in SEED_SOCKETS[_letter]["map"].items()},
             side="B", ref_=f"J_SEED_{_letter}", lcsc="C59983", desc=f"socket for the Seed bank {_letter}")

# ================================================================== AUDIO (Seed codec: Seed2 DFM Fig. 1.3 in / Fig. 1.5 out)
with blk("Audio_Seed", "audio_seed"):
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
with blk("Audio_Ext", "audio_ext"):
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

# ================================================================== CV IN (Dev Kit stage, 4 channels)
with blk("CV_In", "cv_in"):
    # CV in x4 (Dev Kit): 100K in, 200K from -10V_REF, 33K || 1nF feedback, MCP6004 on +3V3A: +-5 V -> 3.3 .. 0 V (inverted: firmware). FOR +-10 V: change the input / reference resistors here.
    for i in range(1, N_CVIN + 1):
        with grp(f"cvin{i}"):
            jack(f"CVIN{i}", f"CVIN{i}_TIP")
            R("100K", f"CVIN{i}_TIP", f"CVIN{i}_INV")
            R("200K", "-10V_REF", f"CVIN{i}_INV")
            R("33K", f"CVIN{i}_INV", f"CV_IN_{i}_ADC")
            C("1nF", f"CVIN{i}_INV", f"CV_IN_{i}_ADC")
    part("U", "Amplifier_Operational:MCP6004", FP_SOIC14, "MCP6004", {
        "3": "GND", "2": "CVIN1_INV", "1": "CV_IN_1_ADC",
        "5": "GND", "6": "CVIN2_INV", "7": "CV_IN_2_ADC",
        "10": "GND", "9": "CVIN3_INV", "8": "CV_IN_3_ADC",
        "12": "GND", "13": "CVIN4_INV", "14": "CV_IN_4_ADC",
        "4": "+3V3A", "11": "GND"}, lcsc="?", ref_="U_CVI1")
    bypass("+3V3A", 1)

with blk("CV_In", "gate_in"):
    # gate in x2 + clock in (Dev Kit): 100K, MMBT3904, 1M, 10K pull-up, 100R (inverted: a high gate reads 0)
    for name, netname in GATES_IN:
        with grp(name):
            jack(name, f"{name}_TIP")
            R("100K", f"{name}_TIP", f"{name}_B")
            R("1M", f"{name}_B", "GND")
            R("10K", "+3V3", f"{name}_C")
            R("100R", f"{name}_C", netname)
            part("Q", "Transistor_BJT:MMBT3904", FP_SOT23, "MMBT3904", {"B": f"{name}_B", "E": "GND", "C": f"{name}_C"}, lcsc=LCSC[("U", "MMBT3904")])

# ================================================================== CV OUT (MCP4728 on I2C, control rate) + gate / clock out
with blk("CV_Out", "cv_out"):
    # MCP4728 quad 12-bit DAC, I2C 0x60 (address bits 000), VDD = 3V3, internal 2.048 V reference at gain 1: channels A and B are CV out 1 / 2, C and D spare. LDAC low (update at once).
    part("U", "Analog_DAC:MCP4728", "Package_SO:MSOP-10_3x3mm_P0.5mm", "MCP4728", {
        "1": "+3V3", "2": "I2C_SCL", "3": "I2C_SDA", "4": "GND", "5": None,
        "6": "CV_OUT_1_DAC", "7": "CV_OUT_2_DAC", "8": None, "9": None, "10": "GND"}, lcsc=LCSC[("U", "MCP4728")], ref_="U_DAC1")
    bypass("+3V3", 1)
    C("10uF", "+3V3", "GND", fp=FP_C0805)
    # CV out x2 (Dev Kit stage, new gain): DAC -> TL074 non-inverting, Rf / Rg (see CVO_RF / CVO_RG): 0 .. 5 V, 100R
    for i in (1, 2):
        with grp(f"cvout{i}"):
            jack(f"CVOUT{i}", f"CVOUT{i}_TIP", sw=None)
            R(CVO_RG, f"CVO{i}_INV", "GND")
            R(CVO_RF, f"CVO{i}_INV", f"CVO{i}_OUT")
            R("100R", f"CVO{i}_OUT", f"CVOUT{i}_TIP")
    part("U", "Amplifier_Operational:TL074", FP_SOIC14, "TL074", {
        "3": "CV_OUT_1_DAC", "2": "CVO1_INV", "1": "CVO1_OUT",
        "5": "CV_OUT_2_DAC", "6": "CVO2_INV", "7": "CVO2_OUT", "4": "+12V", "11": "-12V"}, lcsc="?", ref_="U_CVO1")
    bypass("+12V", 1)
    bypass("-12V", 1)

with blk("CV_Out", "gate_out"):
    # gate out x2 + clock out: 74AHCT1G125 on +5 V, 100K pull-down on the GPIO, 1K to the tip: 0 / 5 V
    for name, netname in GATES_OUT:
        with grp(name):
            jack(name, f"{name}_TIP", sw=None)
            R("100K", netname, "GND")
            part("U", "74xGxx:74AHCT1G125", FP_SOT23_5, "74AHCT1G125",
                 {"1": "GND", "2": netname, "3": "GND", "4": f"{name}_BUF", "5": "+5V"}, lcsc=LCSC[("U", "74AHCT1G125")])
            R("1K", f"{name}_BUF", f"{name}_TIP")
            bypass("+5V", 1)

# ================================================================== MIDI (TRS type A)
with blk("MIDI", "midi"):
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

# ================================================================== DIGITAL I/O: expanders, LED drivers, analog mux
with blk("Digital_IO", "io"):
    ENC = [(f"ENC{i}_A", f"ENC{i}_B", f"ENC{i}_SW") for i in range(1, 5)]
    BTN = [f"BTN{i}" for i in range(1, N_BTN + 1)]
    MX = [f"MX{i}" for i in range(1, 9)]
    io1 = [s for e in ENC for s in e] + BTN[:4]               # 12 + 4 = 16
    io2 = BTN[4:] + MX                                          # 6 + 8 = 14 (2 spare)
    io3 = ["MUX_A", "MUX_B", "MUX_C", "LED_OE", "OLED_RES"]    # outputs (firmware sets them); 11 spare. They left the Seed to free its pins.
    for ref_, a, sigs in (("U_IO1", (0, 0, 0), io1), ("U_IO2", (1, 0, 0), io2), ("U_IO3", (0, 1, 0), io3)):      # 0x20, 0x21, 0x22
        pins = {"V_{DD}": "+3V3", "V_{SS}": "GND", "SCK": "I2C_SCL", "SDA": "I2C_SDA",
                "A0": "+3V3" if a[0] else "GND", "A1": "+3V3" if a[1] else "GND", "A2": "+3V3" if a[2] else "GND", "~{RESET}": "+3V3",
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
    if OLED_MODEL == "0.96":
        R("10K", "+3V3", "OLED_RES")                   # the 0.96 in module has a RES pin: not held in reset until the firmware drives it

with blk("Digital_IO", "leddrv"):
    # LED drivers: PCA9685 open drain, LED anodes on +5V_LED, resistors in series with the cathodes (on the panel sheet). 0x40: BTN1-5 RGB (15) + PTL1. 0x41: BTN6-10 RGB (15) + PTL2.
    names = [f"LED_BTN{i}_{c}" for i in range(1, 6) for c in "RGB"] + ["LED_PTL1"]
    names += [f"LED_BTN{i}_{c}" for i in range(6, 11) for c in "RGB"] + ["LED_PTL2"]
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

with blk("Digital_IO", "mux"):
    # panel analog: 74HC4051 on +3V3A, selects from U_IO3. 0 PTL1 | 1 PTL2 | 2 slider | 3 POT1 | 4 POT2 | 5 POT3 | 6 POT4 | 7 free
    part("U", "74xx:74HC4051", FP_SOIC16, "74HC4051",
         {"A0": "WIP_PTL1", "A1": "WIP_PTL2", "A2": "WIP_SL", "A3": "WIP_POT1", "A4": "WIP_POT2",
          "A5": "WIP_POT3", "A6": "WIP_POT4", "A7": None, "A": "POT_MUX", "S0": "MUX_A", "S1": "MUX_B", "S2": "MUX_C",
          "~{E}": "GND", "VEE": "GND", "GND": "GND", "VCC": "+3V3A"}, lcsc="?", ref_="U_MUX1")
    bypass("+3V3A", 1)
    C("10nF", "POT_MUX", "GND")

# ================================================================== DISPLAY (OLED_MODEL picks the module; the other one stays in KicadLibs)
if OLED_MODEL == "1.3":
    OLED_WINDOW = (32.0, 17.5, 8.9, 12.7)           # w, h and the centre in the module frame (viewing area 31.42 x 16.70 + margins), for the faceplate
else:
    OLED_WINDOW = (24.0, 12.8, 7.62, 10.21)         # viewing area 22.74 x 11.86 + 0.6 each side
with blk("Display", "oled"):
    if OLED_MODEL == "1.3":      # HS13L01W4S01: SH1106, 8-pin header, NO reset pin, FS0 / CS2 = font chip (unused)
        part("J", "Display_OLED:OLED_HS13L01W4S01", "Daisy_Seed_Misc:OLED_1.3in_SPI_Module_HS13L01W4S01", "HS13L01W4S01",
             {"GND": "GND", "VCC": "+3V3", "SCL": "OLED_SCK", "SDA": "OLED_MOSI", "DC": "OLED_DC", "CS1": "GND", "FS0": None, "CS2": None},
             side="T", ref_="J_OLED1", lcsc="C5139764")
    else:                        # HS96L01W4S03: SSD1315, 7-pin header; CS tied low (the OLED is alone on SPI1), RES from the third expander
        part("J", "Display_OLED:OLED_HS96L01W4S03", "Daisy_Seed_Misc:OLED_0.96in_SPI_Module_HS96L01W4S03", "HS96L01W4S03",
             {"GND": "GND", "VCC": "+3V3", "SCL": "OLED_SCK", "SDA": "OLED_MOSI", "RES": "OLED_RES", "DC": "OLED_DC", "CS": "GND"},
             side="T", ref_="J_OLED1", lcsc="C5139758")
    C("10uF", "+3V3", "GND", fp=FP_C0805)
    bypass("+3V3", 1)

# ================================================================== PANEL (front side, hand soldered)
TL1 = ("OK_Switch:SW_Tact_RGB_Lakeview_TL1-DNNFN-RCWN", "OK_Switch:SW_Tact_RGB_Lakeview_TL1-DNNFN-RCWN_THT", "TL1-DNNFN-RCWN RGB", "C39501039")        # cap dia 5.6, 16.4 mm high
TL16 = ("OK_Switch:SW_Tact_RGB_Lakeview_TL16-NND6W-FN", "OK_Switch:SW_Tact_RGB_Lakeview_TL16-NND6W-FN_THT", "TL16-NND6W-FN RGB", "C55788158")      # cap dia 9, 14.35 mm high
with blk("Panel", "enc"):
    for i in range(1, 5):                      # 4 standard Bourns encoders, 20 mm shaft (the 15 mm bushing is too short for a nut), with push switch
        part("ENC", "OK_Encoder:Encoder_Bourns_PEC11R_S", "OK_Encoder:Encoder_Bourns_PEC11R-4x20K-S_THT", "PEC11R-4220K-S0024",
             {"A": f"ENC{i}_A", "B": f"ENC{i}_B", "C": "GND", "S1": f"ENC{i}_SW", "S2": "GND"}, side="T", ref_=f"ENC{i}")

with blk("Panel", "btn"):
    for i in range(1, N_BTN + 1):              # 10 Lakeview RGB buttons, common anode on +5V_LED: TL1 for 1-8, TL16 for 9-10 (slider section)
        with grp(f"btn{i}"):
            symb, fpb, valb, lcscb = TL16 if i >= 9 else TL1
            if i >= 9:                             # TL16: contacts 1+2 and 3+4
                sw = {"1": f"BTN{i}", "2": f"BTN{i}", "3": "GND", "4": "GND"}
            else:                                  # TL1: contacts 1+3 and 2+4
                sw = {"1": f"BTN{i}", "3": f"BTN{i}", "2": "GND", "4": "GND"}
            part("SW", symb, fpb, valb, {**sw, "R": f"LED_BTN{i}_R_LK", "G": f"LED_BTN{i}_G_LK", "B": f"LED_BTN{i}_B_LK", "C+": "+5V_LED"}, side="T", ref_=f"SW_BTN{i}", lcsc=lcscb)
            R("330R", f"LED_BTN{i}_R_K", f"LED_BTN{i}_R_LK")        # the PCA9685 sinks each colour; no LED data in the datasheets: CHECK the currents on a sample
            R("220R", f"LED_BTN{i}_G_K", f"LED_BTN{i}_G_LK")
            R("220R", f"LED_BTN{i}_B_K", f"LED_BTN{i}_B_LK")

with blk("Panel", "mx"):
    # 8 Cherry MX + SK6812-EC20 (one footprint each): LED_DATA -> 74AHCT1G125 on +5V_LED (a 3.3 V data line is out of spec for a 5 V SK6812 chain) -> 33R -> key 1 ... key 8
    part("U", "74xGxx:74AHCT1G125", FP_SOT23_5, "74AHCT1G125",
         {"1": "GND", "2": "LED_DATA", "3": "GND", "4": "LED_DATA_5V", "5": "+5V_LED"}, lcsc=LCSC[("U", "74AHCT1G125")], ref_="U_LS1")
    R("33R", "LED_DATA_5V", "MXL_DIN1")
    bypass("+5V_LED", 1)
    for i in range(1, 9):
        with grp(f"mx{i}"):
            part("SW", "Senario:SW_MX_SK6812", "OK_Switch:SW_Cherry_MX_SK6812-EC20", "Cherry MX + SK6812-EC20",
                 {"1": f"MX{i}", "2": "GND", "3": "GND", "4": "MXL_DIN1" if i == 1 else f"MXL_DOUT{i - 1}", "5": "+5V_LED", "6": f"MXL_DOUT{i}" if i < 8 else None},
                 side="T", ref_=f"SW_MX{i}")
            C("100nF", "+5V_LED", "GND")                            # one bypass per LED

with blk("Panel", "sliders"):
    for i in (1, 2):                           # Bourns PTL20 slide pots with LED
        part("PTL", "Bourns_PTL:PTL20", "Bourns_PTL:Bourns_PTL20_Slide_LED", "PTL20-15R 10K",
             {"1": "GND", "2": f"WIP_PTL{i}", "3": "+3V3A", "E": f"LED_PTL{i}_K", "B": f"LED_PTL{i}_A", "L": None},
             side="T", ref_=f"PTL{i}")
        R("330R", "+5V_LED", f"LED_PTL{i}_A")
    part("SL", "4ms_Potentiometer:Pot_Slider_60mm_10k", "Daisy_Seed_Misc:ALPS-RS6011_60mm_Panel", "Alps RS6011 60mm 10K",
         {"1": "GND", "2": "WIP_SL", "3": "+3V3A", "4": None, "5": None, "6": None, "7": None, "8": None}, side="T", ref_="SL1")

with blk("Panel", "pots"):
    for i, (fpp, valp, lcscp) in enumerate((("OK_Pot:Pot_Rotary_Alps_RK09K-knurl20_THT", "RK09K1130A5R 10K linear (trim, knurled 20 mm)", "C209779"),
                                           ("OK_Pot:Pot_Rotary_Alps_RK09K-knurl20_THT", "RK09K1130A5R 10K linear (trim, knurled 20 mm)", "C209779"),
                                           ("OK_Pot:Pot_Rotary_Alpha_RD901F-flat15_THT", "RD901F-40-15F-B10K-00DL1 (regular)", None),
                                           ("OK_Pot:Pot_Rotary_Alpha_RD901F-flat15_THT", "RD901F-40-15F-B10K-00DL1 (regular)", None)), 1):
        part("VR", "OK_Pot:Pot_Rotary_Alps_RK09", fpp, valp, {"1": "GND", "2": f"WIP_POT{i}", "3": "+3V3A"}, side="T", ref_=f"VR{i}", lcsc=lcscp)      # VR1 / VR2 trim (Alps RK09K A5R, knurled 20 mm, C209779), VR3 / VR4 regular

# mounting holes (M2.5, in the corners)
with blk("Power", "holes"):
    for i in range(1, 7):                      # H1-H4 at the sides / corners, H5 and H6 in the middle of the board, between the buttons of the button row
        part("H", "Mechanical:MountingHole", "MountingHole:MountingHole_2.7mm_M2.5", "M2.5", {}, side="T", ref_=f"H{i}")

# Parts left out of the PCB placement for now (the schematic keeps them). Set to () to bring them back.
PCB_HIDE_REFS = ()                                                       # nothing hidden: pots are above the PTL sliders, buttons around the slider
PCB_HIDE_NETS = ()                                                       # (nothing else hidden)


def pcb_hidden(p):
    """True for parts that are in the schematic but not (yet) on the board or in the BOM."""
    if any(p["ref"].startswith(x) for x in PCB_HIDE_REFS):
        return True
    return p["ref"].startswith("R") and any(str(n).startswith(PCB_HIDE_NETS) for n in p["pins"].values() if n)


# ================================================================== FLOORPLAN (front side, mm, origin = board top-left)
# 24HP: panel 121.92 nominal (about 121.55 real). Board 120 x 108: height = 128.5 panel - 2 x 10 mm rail clearance - 0.5
# (community rule: board <= 108..110 mm, parts 10 mm clear of the top and bottom edges of the panel; see docs/design-notes.md)
BOARD = dict(w=121.0, h=108.0)                         # 121.0: 0.25 mm inside the 24HP panel (121.5) on each side (was 120.0); the placement below is drawn on a 120 wide board and shifted by X_SHIFT = 0.5 at the end of the FLOOR block
FLOOR = OrderedDict()
# INITIAL PLACEMENT (2026-11-22): a starting point for the hand pass, NOT a finished layout. With 22 jacks + OLED + 4 encoders + 10 buttons + MX 4 x 2 + 3 sliders + 4 pots the front is
# full: expect a few overlaps (run the build: it prints the courtyard overlaps of the front parts). Plan: jacks in one full-width band (11 columns of 2, inputs left, outputs right);
# OLED in the middle of the encoder band with 2 encoders on each side (spec-beta.md option A); the MX matrix and the Alps slider below; the two edge strips (x < 9 mm and x > 111 mm)
# hold the USB-C, the microSD slot and the six control buttons; the side columns (x = 14.8 and 105.2) hold the PTL20, the tall trim and the regular pot.
# step 16: the columns of the placed jacks are JACK_PITCH_MONO = 9.7 apart = the courtyard width (-4.8 .. +4.9), no gap between neighbouring courtyards (was 10.0, 0.3 mm). Check the hex nuts on the panel before keeping it.
# JACK PITCH, condensed (2026-11-22): the courtyards are 9.69 (mono Thonkiconn) / 10.59 (stereo MIDI) wide and 13.47 tall; the pitches leave 0.3 mm between neighbouring courtyards at the tightest pair
# (a mono jack next to a MIDI jack: 10.14 + 0.3 = 10.44, rounded up) and 0.33 mm between the two rows. Was 10.8 x 15.0.
JACK_PITCH_X, JACK_PITCH_Y = 10.45, 13.47           # step 14: the rows 13.47 apart (was 13.8): the jack courtyards (13.47 tall) touch, no gap between them
JX = [60.0 + (i - 5) * JACK_PITCH_X for i in range(11)]              # 11 columns, centred on the board
JY = [7.5, 7.5 + JACK_PITCH_Y]
_grid = [  # (row, col): jack. Left block = 6 columns of inputs, right block = 5 columns of outputs; two jacks per column
    (0, 0, "AIN1"), (1, 0, "AIN2"),            # audio in 1, 2 (Seed codec)
    (0, 1, "AIN3"), (1, 1, "AIN4"),            # audio in 3, 4 (PCM3060)
    (0, 2, "CVIN1"), (1, 2, "CVIN2"),
    (0, 3, "CVIN3"), (1, 3, "CVIN4"),
    (0, 4, "GATEIN1"), (1, 4, "GATEIN2"),
    (0, 5, "CLKIN"), (1, 5, "MIDIIN1"),
    (0, 6, "AOUT1"), (1, 6, "AOUT2"),          # out main L, R
    (0, 7, "AOUT3"), (1, 7, "AOUT4"),          # out send L, R
    (0, 8, "CVOUT1"), (1, 8, "CVOUT2"),
    (0, 9, "GATEOUT1"), (1, 9, "GATEOUT2"),
    (0, 10, "CLKOUT"), (1, 10, "MIDIOUT1"),
]
for r_, c_, n in _grid:
    FLOOR["J_" + n] = (JX[c_], JY[r_], 90)
# AUDIO jacks (the only jacks placed so far): the mono Thonkiconn courtyard is 9.69 wide, so JACK_PITCH_MONO = 10.0 leaves 0.31 mm between neighbours; the inputs at the far left, the outputs at the far right
# (the same distance to the board edge on both sides, aligned with the gate inputs). The MIDI jacks (10.59 wide) need 10.45 next to them: JACK_PITCH_X above is for when they come back.
JACK_PITCH_MONO, JACK_EDGE_X = 9.7, 4.9                 # JACK_EDGE_X = GATE_STRIP_X: the outer jack columns of the top block are on the same vertical lines as the gate-in jacks
# columns of two jacks (top, bottom), from the left edge for the inputs and from the right edge for the outputs
JACK_COLS_IN = (("AIN1", "AIN2"), ("AIN3", "AIN4"), ("CVIN1", "CVIN2"), ("CVIN3", "CVIN4"))                 # audio in 1-4, CV in 1-4
JACK_COLS_OUT = (("AOUT3", "AOUT4"), ("AOUT1", "AOUT2"), ("CVOUT1", "CVOUT2"), ("GATEOUT1", "GATEOUT2"))    # from the far right: audio out 3-4, 1-2, CV out 1-2, gate out 1-2
for _k, (_a, _b) in enumerate(JACK_COLS_IN):
    FLOOR["J_" + _a] = (JACK_EDGE_X + _k * JACK_PITCH_MONO, JY[0], 90)
    FLOOR["J_" + _b] = (JACK_EDGE_X + _k * JACK_PITCH_MONO, JY[1], 90)
for _k, (_a, _b) in enumerate(JACK_COLS_OUT):
    FLOOR["J_" + _a] = (120.0 - JACK_EDGE_X - _k * JACK_PITCH_MONO, JY[0], 90)
    FLOOR["J_" + _b] = (120.0 - JACK_EDGE_X - _k * JACK_PITCH_MONO, JY[1], 90)
# THIRD ROW (step 7): clock in under the first input column, clock out under the first output column: the same vertical lines as the audio jacks and the gate inputs, one row pitch below the second row
ENC_Y = JY[1] + 14.4                                          # y of the encoder shafts AND of the clock jacks (step 10): 14.4 below the second jack row (the other rows are 13.8 apart); 35.4 fails DRC, see ENCODERS below
CLK_Y = ENC_Y + 15.4                                         # step 18: the clock jacks go down the edge columns, under the trimmers (their courtyards touch the trimmer courtyards)
FLOOR["J_CLKIN"] = (JACK_EDGE_X, CLK_Y, 90)                 # step 10: on the horizontal axis of the encoder shafts (ENC_Y, 37.4; was one row pitch below the second row = 35.1)
FLOOR["J_CLKOUT"] = (120.0 - JACK_EDGE_X, CLK_Y, 90)
# BOTTOM (step 8): MIDI in under the left column, MIDI out under the right column, on the same vertical lines (like the gate inputs); the y is the lowest that keeps the jack on the board
MIDI_Y = 101.0
FLOOR["J_MIDIIN1"] = (JACK_EDGE_X, MIDI_Y, 90)
FLOOR["J_MIDIOUT1"] = (120.0 - JACK_EDGE_X, MIDI_Y, 90)
COL_L, COL_R = 15.3, 120.0 - 15.3                     # the pot / PTL slider columns
STRIP_L, STRIP_R = 4.5, 120.0 - 4.5                   # the edge strips
_OLED_HALF_H = 14.15 if OLED_MODEL == "0.96" else 17.0         # half the courtyard height of the module (28.3 for the 0.96 in, 34.0 for the 1.3 in)
OLED_CX, OLED_CY = 60.0, 0.5 + _OLED_HALF_H                   # OLED (step 5): centred on the board, its courtyard 0.5 mm from the top edge, header up (the window is near the top)
_OLED_C = (7.62, 12.58) if OLED_MODEL == "0.96" else (8.9, 14.75)        # module centre relative to the footprint origin (pin 1)
FLOOR["J_OLED1"] = (OLED_CX - _OLED_C[0], OLED_CY - _OLED_C[1], 0)
# USB-C and microSD (step 9, moved beside the OLED): USB-C (long side vertical) at the left of the display, the vertical microSD slot at the right, each centred in the free column between the OLED courtyard
# (x 46.6 .. 74.4 on the board) and the CV in 3-4 / gate-out jacks (courtyards end at x 40.3, start at x 80.8), on the OLED's vertical centre. The gap is 6.3 mm left and 6.4 mm right: the USB-C (5.0 wide) fits,
# the microSD courtyard (6.94 wide) overlaps its neighbours by ~0.27 mm each side (COURTYARD_OK, the bodies clear)
_OLED_HALF_W = 13.95                                           # half the OLED courtyard width (27.9)
_USB_X = ((JACK_EDGE_X + 3 * JACK_PITCH_MONO + 4.9) + (OLED_CX - _OLED_HALF_W)) / 2             # middle of the free column left of the OLED (courtyard of the 4th input column ends at +4.9)
_SD_X = ((120.0 - JACK_EDGE_X - 3 * JACK_PITCH_MONO - 4.8) + (OLED_CX + _OLED_HALF_W)) / 2     # and right of it (courtyard of the 4th output column starts at -4.8)
# OLED on the FACEPLATE (step 10): the module hangs from the faceplate (4 screws through the faceplate, spacers between), so its 4 mounting holes are in the faceplate and NOT on the carrier:
# no unplated holes under the encoders 2 and 3 any more (they allowed the encoders to go no higher than 37.4; with the holes off the carrier: 36.0). The carrier keeps the pin header only.
OLED_ON_FACEPLATE = True
OLED_HOLES = ([(-4.03, 0.68), (-4.03, 24.48), (19.27, 0.68), (19.27, 24.48)], 2.7) if OLED_MODEL == "0.96" else ([(-6.3, 0.5), (-6.3, 29.0), (24.1, 0.5), (24.1, 29.0)], 3.0)   # mounting holes in the footprint frame, hole diameter
# Vertical position: the TOP EDGES of the faceplate openings (OLED window, USB-C slot, microSD slot) are on one line, the top edge of the OLED window
USB_SLOT_L, SD_SLOT_L = 9.6, 13.6                              # length of the two faceplate openings (gen_faceplate.py), both long side vertical
OLED_WIN_TOP = FLOOR["J_OLED1"][1] + OLED_WINDOW[3] - OLED_WINDOW[1] / 2
FLOOR["J_USB1"] = (_USB_X + 0.2, OLED_WIN_TOP + USB_SLOT_L / 2, 90)
FLOOR["J_SD1"] = (_SD_X + 0.55, OLED_WIN_TOP + SD_SLOT_L / 2 + 0.4, 90)    # the faceplate slot is 0.4 mm from the footprint origin along its x (-y on the board at 90 deg); the origin is also -0.55 from the courtyard centre in x
SL_Y = 91.9                                           # SLIDER BLOCK (step 1; 91.4 until step 15: the whole block above the control buttons moved 0.5 mm down, to clear the Alpha pots from the PTL sliders): the Alps slider (lever on this line) with a TL16 on each side, above the row of control buttons
MX_EXTRA = 0.3                                        # the MX caps are this much further from the lever than the control-button caps are (8.3 + 0.3 = 8.6 mm): a little more air above the slider
MX_PITCH, MX_CAP = 18.5, 18.2                         # key pitch (standard MX: 19.05, caps 18.2 wide: a 0.85 mm gap); 18.5 leaves 0.3 mm between the caps
KX = [60.0 - 1.5 * MX_PITCH + MX_PITCH * i for i in range(4)]
BTN_CAP_R = 2.8                                        # TL1 cap dia 5.6
_BTN_ROW_Y = 102.5
_GAP = 8.3                                            # (was (_BTN_ROW_Y - BTN_CAP_R) - SL_Y = 8.3; since step 15 the block moves down by itself and the control buttons stay, so the lever to the control button caps is 7.8 now)                 # lever (slider centre line, SL_Y) to the top edge of the control-button caps: 8.3 mm
_MX_BOTTOM = SL_Y - _GAP - MX_EXTRA                               # the MX cap bottom edge is the SAME distance above the lever: a slider cap centred on the lever has equal space to the keys and to the buttons
KY = [_MX_BOTTOM - MX_CAP / 2 - MX_PITCH, _MX_BOTTOM - MX_CAP / 2]       # MX MATRIX (step 2): above the slider block
for n in range(8):
    FLOOR[f"SW_MX{n + 1}"] = (KX[n % 4], KY[n // 4], 180)                 # turned 180: the LED faces up
# ENC_Y (set above, with the clock jacks). ENCODERS (step 4): one row above the MX matrix (since step 11 NOT on the key axes: see ENC_PITCH); 35.7 is the highest y where the PEC11R switch pads (shaft y - 7.9) clear the tip pads of CV in 4 / gate out 2 (bottom y 27.5; 35.4 gives a clearance error, 35.1 a short) once the OLED holes are off the carrier (with them on it: 37.4), and the keycaps (top 46.1)
ENC_PITCH = 16.4                                      # step 11: the encoders are closer together and no longer on the key axes: centred on the board, this pitch apart (the PEC11R lug pads are 16.0 wide over all: 16.4 leaves 0.4 mm between the pads of neighbours)
for _i in range(4):
    FLOOR[f"ENC{_i + 1}"] = (60.0 + (_i - 1.5) * ENC_PITCH, ENC_Y, 0)
# POTS (step 12, a TRIAL placement): the two Alpha RD901F pots (VR3, VR4) one on each side, between the clock jack and the first encoder (free x 10.3 .. 27.5 on the board), on the encoder axis.
# The two Alps trims (VR1, VR2: RK09K A5R, knurled 20 mm, C209779) are placed in step 18 (edge columns, where the clock jacks were).
POT_X, POT_Y = 20.7, 33.9                             # step 23: the Alpha pots turned 90 deg (pins outward: left pot 90, right pot 270) so their 12.4 mm lug span runs vertically between the second jack row (pad tails end 27.2) and the PTL (starts 40.6);
FLOOR["VR3"] = (POT_X, POT_Y, 90)                     # they no longer follow the encoder axis or the trimmers. Plan x 20.7 = board 21.2: pins side 12.8 (trimmer ends 11.95), far edge 26.1 (the encoder starts 27.9)
FLOOR["VR4"] = (120.0 - POT_X, POT_Y, 270)
# TRIMMERS (step 18): where the clock jacks were, in the edge columns (1.5 mm above the encoder axis, steps 19-22); turned 180 (pins down, away from the second jack row), x = 6.15 on the board = the lug pads 0.35 mm inside the board edge
TRIM_Y = ENC_Y - 1.5                                          # 1.5 mm above the encoder axis (0.5 in step 19, 0.5 more in step 20, 0.3 in step 21, 0.2 in step 22): the trimmers do not follow it any more
FLOOR["VR1"] = (5.65, TRIM_Y, 180)
FLOOR["VR2"] = (120.0 - 5.65, TRIM_Y, 180)
FLOOR["SL1"] = (60.0, SL_Y, 0)                        # Alps RS6011 60 mm: body about 76 x 10
SIDE_XL, SIDE_XR = 14.5, 105.5                        # the axis of the TL16 buttons: the side blocks are centred on it (14.0 / 106.0 until step 13: moved 0.5 mm toward the centre in two steps)
FLOOR["SW_BTN9"] = (SIDE_XL, SL_Y, 0)                 # TL16 (cap 9 mm) beside the Alps slider (body x 22 .. 98)
FLOOR["SW_BTN10"] = (SIDE_XR, SL_Y, 0)
# SIDE BLOCKS (step 3), bottom to top on each side: one control button (TL1) and one PTL20 slider, on the axis of the TL16. Every gap (cap edge to cap edge, cap edge to slot end) is SIDE_GAP.
SIDE_GAP, TL16_R, PTL_HALF_SLOT = 9.6, 4.5, 11.8                   # the PTL slot is 23.6 long; 9.6 is the smallest gap at which the PTL body (7.45 beyond each slot end) clears the TL1 body (0.3 mm): 8.3 would overlap by 1.0 mm
_SIDE_BTN_Y = _MX_BOTTOM - BTN_CAP_R                  # the control button: its cap BOTTOM EDGE on the line of the MX keycap bottom edge
SIDE_BODY_GAP, TL1_BODY_H, PTL_BODY_H = 1.0, 3.75, 17.5              # the REAL bodies (F.Fab outlines): TL1 7.5 square, PTL20 35.0 long (its courtyard, 38.4, has 1.7 mm of margin at each end); the slider body ends SIDE_BODY_GAP above the button body (1.0 = the PTL20 clearance: courtyard 37.0 = body 35.0 + 1 mm each end)
_SIDE_PTL_Y = _SIDE_BTN_Y - TL1_BODY_H - SIDE_BODY_GAP - PTL_BODY_H
COURTYARD_OK = {("PTL1", "SW_BTN7"), ("PTL2", "SW_BTN8"),                                      # courtyards that overlap ON PURPOSE (the bodies clear each other): no warning, no DRC error
                ("J_GATEIN1", "SW_BTN7"), ("J_GATEIN1", "SW_BTN9"), ("J_GATEIN1", "PTL1"), ("J_GATEIN2", "SW_BTN8"), ("J_GATEIN2", "SW_BTN10"), ("J_GATEIN2", "PTL2"),
                ("J_CLKIN", "PTL1"), ("J_CLKOUT", "PTL2"), ("J_MIDIIN1", "SW_BTN9"), ("J_MIDIOUT1", "SW_BTN10"),
                ("ENC2", "J_OLED1"), ("ENC3", "J_OLED1"),
                ("ENC1", "J_CVIN2"), ("ENC1", "J_CVIN4"), ("ENC4", "J_CVOUT2"), ("ENC4", "J_GATEOUT2"),
                ("VR3", "PTL1"), ("VR4", "PTL2"), ("VR3", "J_AIN4"), ("VR3", "J_CVIN2"), ("VR3", "VR1"), ("VR4", "J_AOUT2"), ("VR4", "J_CVOUT2"), ("VR4", "VR2"),   # step 23: the Alpha pots: 0.47 mm from the jack pad tails and the PTL, 0.85 from the trimmers (outlines, pads included)
                                      # step 15: the Alpha pot body ends 0.43 mm above the PTL body
                ("ENC1", "ENC2"), ("ENC2", "ENC3"), ("ENC3", "ENC4")}   # step 11: neighbouring encoders: the courtyards (16.9 wide, margin around the lugs) overlap, the lug pads are 0.4 mm apart               # step 10: the encoder bodies (z <= 6.6) pass under the OLED module (its PCB is above z 8.5), no copper in common
GATE_STRIP_X = 4.9                                    # the gate inputs of the two side buttons (step 6): in the edge strips, centred on the button's line (y); the jack body (9.0 wide) ends 0.1 mm before the PTL body, 0.85 before the TL1 body, 1.1 above the TL16 flange
FLOOR["J_GATEIN1"] = (GATE_STRIP_X, _SIDE_BTN_Y, 90)                    # gate in 1: the left button (BTN7)
FLOOR["J_GATEIN2"] = (120.0 - GATE_STRIP_X, _SIDE_BTN_Y, 90)            # gate in 2: the right button (BTN8)
FLOOR["SW_BTN7"] = (SIDE_XL, _SIDE_BTN_Y, 0)
FLOOR["SW_BTN8"] = (SIDE_XR, _SIDE_BTN_Y, 0)
FLOOR["PTL1"] = (SIDE_XL, _SIDE_PTL_Y, 90)
FLOOR["PTL2"] = (SIDE_XR, _SIDE_PTL_Y, 90)
BTN_ROW_Y = 102.86                                     # CONTROL BUTTONS (step 1): the six TL1 in one aligned row at the bottom edge, 13 mm pitch, centred
BTN_PITCH = 13.0
for _i in range(6):
    FLOOR[f"SW_BTN{_i + 1}"] = (60.0 + (_i - 2.5) * BTN_PITCH, BTN_ROW_Y, 0)
FLOOR["H1"], FLOOR["H2"], FLOOR["H3"], FLOOR["H4"] = [(x, y, 0) for x, y in ((2.0, 61.0), (118.0, 61.0), (16.5, 104.0), (103.5, 104.0))]
FLOOR["H5"] = (45.5, 61.0, 0)
FLOOR["H6"] = (74.5, 61.0, 0)

# ---------------------------------------------------------------- SEQUENTIAL PLACEMENT (from the bottom up)
# Only the parts of the blocks placed so far are on the board; every other front part is PARKED beside it (x > 125, in a grid) until its turn, so the board shows only decisions.
# FLOOR_PROPOSED keeps the earlier full layout (to be re-placed block by block). To place the next block: add its refs to PLACED and give them their positions above.
FLOOR_PROPOSED = OrderedDict(FLOOR)
PLACED = (["J_" + _n for _c in JACK_COLS_IN + JACK_COLS_OUT for _n in _c]        # the 16 jacks of the top band: audio in / out, CV in 1-4, CV out 1-2, gate out 1-2; the gate in, clock and MIDI jacks are parked until their turn
          + [f"SW_BTN{i}" for i in range(1, 7)]                       # step 1a: the six control buttons, bottom row
          + ["SL1", "SW_BTN9", "SW_BTN10"]                            # step 1b: the slider block
          + [f"SW_MX{i}" for i in range(1, 9)]                        # step 2: the 4 x 2 Cherry MX matrix with SK6812 (above the slider block)
          + ["SW_BTN7", "SW_BTN8", "PTL1", "PTL2"]                    # step 3: the side blocks (a control button and a PTL20 slider on each side)
          + [f"ENC{i}" for i in range(1, 5)]                          # step 4: the four encoders above the matrix, on the key-column axes
          + ["J_OLED1"]                                               # step 5: the OLED display, centred at the top of the board
          + ["J_GATEIN1", "J_GATEIN2"]                                # step 6: the gate inputs, in the edge strips beside the side buttons
          + ["J_CLKIN", "J_CLKOUT"]                                   # step 7: clock in / out, the third row of the first column on each side
          + ["J_MIDIIN1", "J_MIDIOUT1"]                               # step 8: MIDI in / out at the bottom of the left / right column
                    + ["J_USB1", "J_SD1"]                                          # step 26: the USB-C at the left of the OLED, the vertical Yamaichi microSD slot at the right (card up through the panel)
          + ["VR3", "VR4", "VR1", "VR2"]                              # step 12: the two Alpha pots (trial: between the clock jacks and the encoders); step 18: the two Alps trimmers in the edge columns
          + ["H3", "H4"])                                             # the bottom corner holes
PARK_X0, PARK_Y0, PARK_DX, PARK_DY, PARK_COLS = 132.0, 8.0, 22.0, 22.0, 5
_k = 0
for _ref in list(FLOOR):
    if _ref not in PLACED:
        FLOOR[_ref] = (PARK_X0 + (_k % PARK_COLS) * PARK_DX, PARK_Y0 + (_k // PARK_COLS) * PARK_DY, FLOOR_PROPOSED[_ref][2])
        _k += 1


X_SHIFT = (BOARD["w"] - 120.0) / 2                    # the floor plan was drawn on a 120 mm wide board (centre x = 60): every placed part moves by this much to stay centred on the wider board
for _ref in PLACED:
    _x, _y, _r = FLOOR[_ref]
    FLOOR[_ref] = (_x + X_SHIFT, _y, _r)


def on_board(ref):
    """True for a front part that is placed on the board (not parked)."""
    return ref not in FLOOR or FLOOR[ref][0] <= BOARD["w"] + 1.0

# back-side parts at a fixed place (x, y, rotation): none now (the microSD slot is on the front, vertical)
BACK_FIXED = {}

ANCHOR = {   # where an SMD block sits when its nets do not say (coarse: the generator places passives behind the control they serve)
    "power": (18, 66), "seed": (60, 70), "audio_seed": (25, 20), "audio_ext": (60, 20), "cv_in": (35, 20), "gate_in": (60, 20), "cv_out": (80, 20), "gate_out": (98, 20),
    "midi": (60, 28), "sd": (110, 51), "ledpwr": (108, 48), "usb": (10, 51), "io": (60, 62), "leddrv": (60, 66), "mux": (60, 58), "oled": (60, 44),
    "enc": (60, 44), "btn": (60, 62), "mx": (60, 80), "sliders": (60, 90), "pots": (60, 50), "holes": (60, 50),
}
ANCHOR = {_k: (_v[0] + X_SHIFT, _v[1]) for _k, _v in ANCHOR.items()}


# Readable titles of the schematic blocks (the heading of each group on its sheet)
BLOCK_TITLES = {
    "power": "Eurorack power input: protection and +12 V / -12 V filtering, +5 V analog, -10 V reference", "seedpwr": "Seed supply: VIN filter (2 x 3R3 + 2 x 100 uF)",
    "ledpwr": "LED supply: 5 V step-down (AP63205)", "holes": "Mounting holes", "seed": "Daisy Seed2 DFM", "seedsock": "Seed sockets (1.27 mm, banks A to E)",
    "usb": "USB-C (D-14D) with ESD protection and CC resistors", "sd": "microSD slot (vertical), 4-bit, Dev Kit wiring",
    "audio_seed": "Audio 1-2: Seed codec, op-amp stages, jacks", "audio_ext": "Audio 3-4: PCM3060 codec, op-amp stages, jacks",
    "cv_in": "CV in 1-4: Dev Kit stage (+-5 V in, 0 .. 3.3 V to the ADC), MCP6004", "gate_in": "Gate in 1-2 and clock in: transistor stage (inverting)",
    "cv_out": "CV out 1-2: MCP4728 DAC (I2C) + Dev Kit op-amp stage (gain: CVO_RF / CVO_RG)", "gate_out": "Gate out 1-2 and clock out: 74AHCT1G125 buffers, 0 / 5 V",
    "midi": "MIDI in / out (TRS type A)", "io": "I/O expanders (MCP23017 x 3): encoders, buttons, MX keys, mux selects, OLED reset",
    "leddrv": "LED drivers (PCA9685 x 2): RGB buttons and PTL20 LEDs", "mux": "Panel analog mux (74HC4051)", "oled": "OLED module",
    "enc": "Encoders (Bourns PEC11R)", "btn": "RGB buttons (Lakeview TL1 x 8, TL16 x 2) with LED resistors", "mx": "MX keys with SK6812 LEDs and the 5 V level shifter",
    "sliders": "Sliders: PTL20 x 2, Alps RS6011 60 mm", "pots": "Pots: trim x 2 (Alps RK09K 20 mm), regular x 2",
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
    "4ms_Jack:EighthInch_PJ398SM": ("${KICADLIBS}/3dmodels/Jack.3dshapes/WQP-PJ398SM.step", (0, 0, 0), (0, 0, -90), (1, 1, 1)),   # the Thonkiconn model, as the 4ms stereo footprint
}
# (the OLED, the Bourns encoders, the pots, the Lakeview buttons, the MX + SK6812 key, the USB-C and the vertical microSD slot use the models of their KicadLibs footprints)

# per-reference model (same footprint, other model): {ref: (file, offset, rotate, scale)}
MODEL_BY_REF = {}
