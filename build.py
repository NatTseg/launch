#!/usr/bin/env python3
"""Build launch-ops Ignition Perspective project — SpaceX style."""
import json, os, shutil, subprocess

SRC = os.path.dirname(os.path.abspath(__file__))
DEST = "/usr/local/ignition/data/projects/launch"

# ── SpaceX palette ──────────────────────────────────────────────────────────
BG    = "#000000"
DARK  = "#080808"
CARD  = "#0D0D0D"
CARD2 = "#121212"
LINE  = "#1A1A1A"
LINE2 = "#252525"
WHT   = "#FFFFFF"
GRY1  = "#AAAAAA"
GRY2  = "#666666"
GRY3  = "#333333"
BLUE  = "#005288"   # SpaceX blue
BLU2  = "#1A90FF"
GRN   = "#00D4AA"   # nominal/go
YLW   = "#FFB300"   # caution
RED   = "#FF3B3B"   # abort
ORG   = "#FF6B00"   # hold

F  = "D-DIN, 'Barlow', 'Helvetica Neue', Arial, sans-serif"
FM = "'D-DIN Exp', 'Share Tech Mono', 'Courier New', monospace"

# ── Primitives ───────────────────────────────────────────────────────────────
def p(x, y, w, h):
    return {"x": x, "y": y, "width": w, "height": h}

def lbl(text, x=0, y=0, w=200, h=24, sz="12px", col=WHT, align="left",
        bold=False, track="normal", upper=False, font=F, wrap=False):
    style = {"color": col, "fontSize": sz, "fontFamily": font,
             "textAlign": align, "letterSpacing": track}
    if bold: style["fontWeight"] = "700"
    if upper: style["textTransform"] = "uppercase"
    props = {"text": text, "style": style}
    if wrap: props["style"]["whiteSpace"] = "pre-wrap"
    return {"type": "ia.display.label",
            "props": props, "meta": {"name": "lbl"},
            "position": p(x, y, w, h)}

def rect(x, y, w, h, bg=LINE, radius=0, border=None):
    style = {"backgroundColor": bg, "borderRadius": f"{radius}px"}
    if border: style["border"] = border
    return {"type": "ia.container.coord",
            "props": {"style": style}, "meta": {"name": "rect"},
            "position": p(x, y, w, h), "children": []}

def btn(text, x, y, w, h, bg="rgba(255,255,255,0.06)", col=WHT,
        border=f"1px solid #303030", sz="11px", radius=1, track="2px"):
    style = {"backgroundColor": bg, "color": col, "fontSize": sz,
             "fontFamily": F, "letterSpacing": track,
             "textTransform": "uppercase", "border": border,
             "borderRadius": f"{radius}px", "cursor": "pointer"}
    return {"type": "ia.input.button",
            "props": {"text": text, "style": style},
            "meta": {"name": "btn"},
            "position": p(x, y, w, h)}

def dot(x, y, col=GRN, r=6):
    style = {"backgroundColor": col, "borderRadius": "50%"}
    return {"type": "ia.container.coord",
            "props": {"style": style}, "meta": {"name": "dot"},
            "position": p(x, y, r, r), "children": []}

def hrule(x, y, w, col=LINE):
    return rect(x, y, w, 1, bg=col)

def vrule(x, y, h, col=LINE):
    style = {"backgroundColor": col}
    return {"type": "ia.container.coord",
            "props": {"style": style}, "meta": {"name": "vrule"},
            "position": p(x, y, 1, h), "children": []}

def coord(children, x=0, y=0, w=1280, h=600, bg=BG, border=None, radius=0):
    style = {"backgroundColor": bg}
    if border: style["border"] = border
    if radius: style["borderRadius"] = f"{radius}px"
    return {"type": "ia.container.coord",
            "props": {"style": style}, "meta": {"name": "coord"},
            "position": p(x, y, w, h),
            "children": children}

def flex_row(children, x=0, y=0, w=1280, h=60, bg=BG, gap=0, pad="0px",
             align="center", justify="flex-start", border=None, radius=0):
    style = {"backgroundColor": bg, "display": "flex", "flexDirection": "row",
             "gap": f"{gap}px", "padding": pad, "alignItems": align,
             "justifyContent": justify}
    if border: style["border"] = border
    if radius: style["borderRadius"] = f"{radius}px"
    return {"type": "ia.container.flex",
            "props": {"direction": "row", "style": style,
                      "justify": justify, "alignItems": align},
            "meta": {"name": "flexrow"},
            "position": p(x, y, w, h),
            "children": children}

def flex_col(children, x=0, y=0, w=1280, h=600, bg=BG, gap=0, pad="0px",
             align="stretch", justify="flex-start"):
    style = {"backgroundColor": bg, "display": "flex", "flexDirection": "column",
             "gap": f"{gap}px", "padding": pad, "alignItems": align,
             "justifyContent": justify}
    return {"type": "ia.container.flex",
            "props": {"direction": "column", "style": style,
                      "justify": justify, "alignItems": align},
            "meta": {"name": "flexcol"},
            "position": p(x, y, w, h),
            "children": children}

def view_embed(path, x, y, w, h):
    return {"type": "ia.display.view",
            "props": {"path": path, "style": {}},
            "meta": {"name": "embed"},
            "position": p(x, y, w, h)}

def status_pill(text, x, y, w=90, h=22, col=GRN):
    c = coord([
        lbl(text, 0, 0, w, h, sz="10px", col=col, align="center",
            bold=True, track="2px", upper=True)
    ], x, y, w, h, bg=BG, border=f"1px solid {col}", radius=1)
    return c

def kpi_card(title, value, sub, col, x, y, w=290, h=100):
    c = coord([
        lbl(title, 16, 14, w-32, 14, sz="10px", col=GRY2, upper=True, track="2px"),
        lbl(value,  16, 34, w-32, 38, sz="32px", col=col, bold=True, font=FM),
        lbl(sub,    16, 76, w-32, 16, sz="11px", col=GRY2),
    ], x, y, w, h, bg=CARD, border=f"1px solid {LINE}", radius=1)
    return c

def mission_row(mission, vehicle, site, date, status, col, y_off):
    sc = {GRN: "GO", YLW: "HOLD", RED: "SCRUB", ORG: "TBD"}.get(col, "GO")
    return coord([
        lbl(mission, 16, 0, 340, 44, sz="13px", col=WHT, align="left"),
        lbl(vehicle, 370, 12, 150, 20, sz="11px", col=GRY1, upper=True, track="1px"),
        lbl(site,    530, 12, 200, 20, sz="11px", col=GRY1, upper=True, track="1px"),
        lbl(date,    740, 12, 180, 20, sz="11px", col=GRY2),
        coord([lbl(sc, 0, 0, 90, 26, sz="10px", col=col, align="center",
                   bold=True, track="2px", upper=True)],
              938, 9, 90, 26, bg=BG, border=f"1px solid {col}", radius=1),
        hrule(0, 43, 1240),
    ], 0, y_off, 1240, 44, bg=BG)

def booster_card(name, flights, status, loc, days, col, x, y, w=220, h=140):
    return coord([
        lbl(name,    14, 14, w-28, 20, sz="16px", col=WHT, bold=True, font=FM),
        lbl(f"FLIGHT {flights}", 14, 38, w-28, 14, sz="10px", col=GRY2, upper=True, track="2px"),
        hrule(14, 60, w-28, LINE2),
        lbl("STATUS",   14, 72, 70, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl(status,     14, 86, 120, 16, sz="12px", col=col, upper=True, track="1px"),
        lbl("LOCATION", 14, 108, 70, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl(loc,        14, 120, w-28, 12, sz="11px", col=GRY2),
    ], x, y, w, h, bg=CARD, border=f"1px solid {LINE}", radius=1)

def pad_card(name, complex_, status, vehicle, next_launch, col, x, y, w=580, h=150):
    return coord([
        lbl(name, 20, 16, 300, 24, sz="18px", col=WHT, bold=True, upper=True, track="3px"),
        lbl(complex_, 20, 44, 300, 14, sz="10px", col=GRY2, upper=True, track="2px"),
        hrule(20, 64, w-40, LINE2),
        lbl("STATUS",      20, 76, 80, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        coord([lbl(status, 0, 0, 110, 22, sz="10px", col=col, align="center",
                   bold=True, track="2px", upper=True)],
              20, 90, 110, 22, bg=BG, border=f"1px solid {col}", radius=1),
        lbl("VEHICLE",     160, 76, 80, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl(vehicle,       160, 90, 200, 22, sz="12px", col=GRY1),
        lbl("NEXT LAUNCH", 20, 120, 100, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl(next_launch,   130, 120, 320, 12, sz="11px", col=GRY2),
    ], x, y, w, h, bg=CARD, border=f"1px solid {LINE}", radius=1)

def ship_card(name, type_, status, loc, mission, col, x, y, w=270, h=160):
    return coord([
        lbl(name,    14, 14, w-28, 20, sz="14px", col=WHT, bold=True, upper=True, track="1px"),
        lbl(type_,   14, 36, w-28, 14, sz="9px",  col=GRY2, upper=True, track="2px"),
        hrule(14, 56, w-28, LINE2),
        lbl("STATUS",   14, 68, 70, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        coord([lbl(status, 0, 0, 90, 22, sz="10px", col=col, align="center",
                   bold=True, track="2px", upper=True)],
              14, 82, 90, 22, bg=BG, border=f"1px solid {col}", radius=1),
        lbl("LOCATION",  14, 112, 70, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl(loc,         14, 126, w-28, 14, sz="11px", col=GRY1),
        lbl("MISSION",   14, 144, 70, 12, sz="9px", col=GRY3, upper=True, track="2px"),  # moved up for h
        lbl(mission,     14, 136, w-28, 14, sz="10px", col=GRY2),
    ], x, y, w, h, bg=CARD, border=f"1px solid {LINE}", radius=1)

# ── View wrapper ─────────────────────────────────────────────────────────────
def view(children, bg=BG):
    return {
        "custom": {},
        "params": {},
        "props": {"defaultSize": {"width": 1280, "height": 900}},
        "root": {
            "type": "ia.container.coord",
            "meta": {"name": "root"},
            "props": {"style": {"backgroundColor": bg}},
            "children": children
        }
    }

# ── resource.json ─────────────────────────────────────────────────────────────
def resource(files):
    return {"scope": "G", "version": 1, "restricted": False, "overridable": True,
            "files": files,
            "attributes": {"lastModification": {"actor": "admin",
                           "timestamp": "2026-06-13T00:00:00Z"}}}

# ── Write helpers ─────────────────────────────────────────────────────────────
def write(rel_path, obj):
    full = os.path.join(SRC, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_view(view_name, children, bg=BG):
    path = f"com.inductiveautomation.perspective/views/{view_name}"
    write(f"{path}/view.json",     view(children, bg))
    write(f"{path}/resource.json", resource(["view.json"]))
    print(f"  wrote {view_name}")

def write_str(rel_path, s):
    full = os.path.join(SRC, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(s)

# ═══════════════════════════════════════════════════════════════════════════════
#  VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

# ── Nav ───────────────────────────────────────────────────────────────────────
def build_nav():
    NAV_H = 60
    children = [
        # Left: logo
        lbl("✦  LAUNCH OPS", 24, 0, 180, NAV_H, sz="13px", col=WHT,
            bold=True, track="3px", upper=True, align="left"),
        vrule(220, 12, 36, GRY3),
        # Nav links
        btn("Overview",  240, 14, 100, 32, bg="transparent",
            border="none", sz="11px", col=GRY1, track="1px"),
        btn("Launches",  348, 14, 100, 32, bg="transparent",
            border="none", sz="11px", col=GRY1, track="1px"),
        btn("Vehicles",  456, 14, 100, 32, bg="transparent",
            border="none", sz="11px", col=GRY1, track="1px"),
        btn("Pads",      564, 14, 80,  32, bg="transparent",
            border="none", sz="11px", col=GRY1, track="1px"),
        btn("Fleet",     652, 14, 80,  32, bg="transparent",
            border="none", sz="11px", col=GRY1, track="1px"),
        # Right: status
        dot(1160, 26, GRN, 8),
        lbl("NOMINAL", 1174, 0, 90, NAV_H, sz="10px", col=GRN,
            track="2px", upper=True, align="left"),
        # bottom border
        hrule(0, NAV_H-1, 1280, LINE2),
    ]
    write_view("Components/Nav", children, BG)

# ── Overview ─────────────────────────────────────────────────────────────────
def build_overview():
    children = []

    # Nav embed
    children.append(view_embed("Components/Nav", 0, 0, 1280, 60))

    # ── Hero: countdown ──────────────────────────────────────────
    hero = coord([
        # bg gradient (fake: just dark)
        lbl("NEXT LAUNCH", 0, 40, 1280, 16, sz="11px", col=GRY2,
            align="center", track="4px", upper=True),
        lbl("T−  00 : 04 : 22 : 17", 0, 68, 1280, 80, sz="72px",
            col=WHT, bold=True, align="center", font=FM, track="4px"),
        lbl("FALCON 9  ·  STARLINK GROUP 10-5  ·  SLC-40, CAPE CANAVERAL",
            0, 158, 1280, 20, sz="13px", col=GRY1, align="center", track="2px", upper=True),
        lbl("NET: JUN 18, 2026  ·  21:45 UTC  ·  WINDOW: INSTANTANEOUS",
            0, 186, 1280, 16, sz="11px", col=GRY2, align="center", track="1px"),
        # Buttons
        btn("WATCH LIVE",      460, 224, 140, 36, bg="rgba(255,255,255,0.06)",
            border=f"1px solid #3A3A3A", sz="11px", col=WHT, track="2px", radius=1),
        btn("MISSION DETAILS", 614, 224, 160, 36, bg="transparent",
            border=f"1px solid #2A2A2A", sz="11px", col=GRY2, track="2px", radius=1),
        hrule(0, 279, 1280, LINE),
    ], 0, 60, 1280, 280, bg=DARK)
    children.append(hero)

    # ── KPI strip ─────────────────────────────────────────────────
    kpi_strip = coord([
        kpi_card("Total Flow Rate",   "244 L / min", "FI-101 + FI-102 combined", BLU2, 20,  10),
        kpi_card("Active Missions",   "7",           "4 Starlink · 2 Commercial · 1 Gov", GRN, 330, 10),
        kpi_card("Fleet Ships",       "6",           "2 ASDS · 4 Support vessels", WHT, 640, 10),
        kpi_card("Launches This Year","42",           "38 Falcon 9  ·  4 Falcon Heavy", YLW, 950, 10),
    ], 0, 340, 1280, 120, bg=BG)
    children.append(kpi_strip)
    children.append(hrule(0, 460, 1280, LINE))

    # ── Upcoming launches table ────────────────────────────────────
    children += [
        lbl("UPCOMING LAUNCHES", 20, 476, 300, 14, sz="10px", col=GRY2,
            upper=True, track="3px"),
        hrule(20, 498, 1240, LINE2),
        # Header row
        coord([
            lbl("MISSION",  16,  0, 340, 24, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl("VEHICLE", 370,  0, 150, 24, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl("SITE",    530,  0, 200, 24, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl("DATE",    740,  0, 180, 24, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl("STATUS",  938,  0,  90, 24, sz="9px", col=GRY3, upper=True, track="2px"),
        ], 20, 506, 1240, 24, bg=BG),
    ]

    launches = [
        ("Starlink Group 10-5",       "Falcon 9",        "SLC-40, CCAFS",  "Jun 18, 2026", GRN),
        ("CRS-33 (SpX-33)",           "Falcon 9",        "LC-39A, KSC",    "Jun 22, 2026", GRN),
        ("Maxar WorldView Legion 3-4", "Falcon 9",       "SLC-4E, VAFB",   "Jun 28, 2026", GRN),
        ("Crew Dragon Endurance (Crew-11)", "Falcon 9",  "LC-39A, KSC",    "Jul 03, 2026", YLW),
        ("Starlink Group 11-1",       "Falcon 9",        "SLC-40, CCAFS",  "Jul 09, 2026", GRN),
        ("GOES-U Weather Satellite",  "Falcon Heavy",    "LC-39A, KSC",    "Jul 14, 2026", ORG),
    ]
    y_start = 534
    for i, (m, v, s, d, col) in enumerate(launches):
        children.append(
            coord([
                lbl(m, 16, 0, 340, 36, sz="12px", col=WHT),
                lbl(v, 370, 8, 150, 20, sz="11px", col=GRY1, upper=True, track="1px"),
                lbl(s, 530, 8, 200, 20, sz="11px", col=GRY1, upper=True, track="1px"),
                lbl(d, 740, 8, 180, 20, sz="11px", col=GRY2),
                coord([lbl({GRN:"GO",YLW:"HOLD",ORG:"TBD",RED:"SCRUB"}.get(col,"GO"),
                           0, 0, 80, 22, sz="10px", col=col, align="center",
                           bold=True, track="2px", upper=True)],
                      938, 7, 80, 22, bg=BG, border=f"1px solid {col}", radius=1),
                hrule(0, 35, 1240, LINE),
            ], 20, y_start + i*36, 1240, 36, bg=BG)
        )

    write_view("Overview", children)

# ── Launches ──────────────────────────────────────────────────────────────────
def build_launches():
    children = []
    children.append(view_embed("Components/Nav", 0, 0, 1280, 60))
    children += [
        lbl("LAUNCH MANIFEST", 24, 84, 400, 28, sz="22px", col=WHT,
            bold=True, upper=True, track="4px"),
        lbl("2026 · MANIFEST SUBJECT TO CHANGE", 24, 116, 500, 16,
            sz="10px", col=GRY2, upper=True, track="2px"),
        hrule(24, 144, 1232, LINE),
    ]

    missions = [
        ("Starlink Group 10-5",       "Falcon 9 B1073.8",  "SLC-40",   "Jun 18",  "21:45 UTC", GRN,  "Booster recovery: OCISLY",       "50th Starlink launch of 2026"),
        ("CRS-33",                    "Falcon 9 B1087.3",  "LC-39A",   "Jun 22",  "14:30 UTC", GRN,  "Booster recovery: LZ-1",         "ISS cargo resupply"),
        ("WorldView Legion 3-4",      "Falcon 9 B1060.18", "SLC-4E",   "Jun 28",  "09:15 UTC", GRN,  "Booster recovery: JRTI",         "Earth imaging constellation"),
        ("Crew-11",                   "Falcon 9 B1077.4",  "LC-39A",   "Jul 03",  "16:00 UTC", YLW,  "Booster recovery: LZ-1",         "4-person ISS crew rotation"),
        ("Starlink Group 11-1",       "Falcon 9 B1058.19", "SLC-40",   "Jul 09",  "03:20 UTC", GRN,  "Booster recovery: OCISLY",       "V2 Mini satellites"),
        ("GOES-U",                    "Falcon Heavy",       "LC-39A",   "Jul 14",  "11:00 UTC", ORG,  "Side core recovery: LZ-1/LZ-2",  "NOAA geostationary weather"),
        ("Starlink Group 10-7",       "Falcon 9 B1062.16", "SLC-40",   "Jul 19",  "02:45 UTC", ORG,  "TBD",                            ""),
        ("Polaris Dawn STS-1",        "Falcon 9 B1091.1",  "LC-39A",   "Aug 04",  "TBD",       ORG,  "Booster recovery: LZ-1",         "Private spacewalk mission"),
    ]

    for i, (name, vehicle, site, date, time_, col, note, sub) in enumerate(missions):
        y = 160 + i * 84
        card = coord([
            # left accent bar
            rect(0, 0, 3, 76, bg=col),
            lbl(name, 20, 12, 480, 22, sz="15px", col=WHT, bold=True),
            lbl(sub,  20, 36, 480, 14, sz="10px", col=GRY2) if sub else lbl("", 0,0,1,1),
            lbl(note, 20, 54, 480, 14, sz="10px", col=GRY3),
            vrule(510, 8, 60, LINE2),
            lbl("VEHICLE", 526, 8,  120, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl(vehicle,   526, 24, 200, 18, sz="12px", col=GRY1),
            lbl("SITE",    526, 48, 120, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl(site,      526, 62, 200, 14, sz="11px", col=GRY2),
            vrule(756, 8, 60, LINE2),
            lbl("DATE",    772,  8, 160, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl(date,      772, 24, 160, 18, sz="16px", col=WHT, bold=True, font=FM),
            lbl(time_,     772, 48, 160, 14, sz="11px", col=GRY2),
            vrule(1000, 8, 60, LINE2),
            lbl("STATUS", 1016,  8, 100, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            coord([lbl({GRN:"GO",YLW:"HOLD",ORG:"TBD",RED:"SCRUB"}.get(col,"GO"),
                       0, 0, 110, 28, sz="11px", col=col, align="center",
                       bold=True, track="2px", upper=True)],
                  1016, 28, 110, 28, bg=BG, border=f"1px solid {col}", radius=1),
        ], 24, y, 1232, 76, bg=CARD, border=f"1px solid {LINE}", radius=1)
        children.append(card)

    write_view("Launches", children)

# ── Vehicles ──────────────────────────────────────────────────────────────────
def build_vehicles():
    children = []
    children.append(view_embed("Components/Nav", 0, 0, 1280, 60))
    children += [
        lbl("VEHICLE STATUS", 24, 84, 500, 28, sz="22px", col=WHT, bold=True, upper=True, track="4px"),
        lbl("FALCON 9 · FALCON HEAVY · STARSHIP", 24, 116, 600, 14,
            sz="10px", col=GRY2, upper=True, track="2px"),
        hrule(24, 144, 1232, LINE),
        lbl("FALCON 9 BOOSTER FLEET", 24, 162, 400, 14, sz="10px",
            col=GRY2, upper=True, track="3px"),
    ]

    boosters = [
        ("B1058", "19", "ACTIVE",      "JRTI — At Sea",          14,  GRN),
        ("B1060", "18", "ACTIVE",      "OCISLY — Port Canaveral",248,  GRN),
        ("B1061", "15", "REFURBISHING","SpaceX Hangar 2, KSC",   482,  YLW),
        ("B1062", "16", "ACTIVE",      "SLC-40, CCAFS",          716,  GRN),
        ("B1067", "14", "ACTIVE",      "SLC-4E, Vandenberg",     950,  GRN),
        ("B1071", "12", "STANDBY",     "SpaceX Hangar, CCAFS",   14,   GRY2),
        ("B1073", "8",  "ACTIVE",      "En route to OCISLY",     248,  GRN),
        ("B1077", "4",  "ACTIVE",      "LC-39A Integration",     482,  GRN),
        ("B1085", "3",  "REFURBISHING","SpaceX Hangar 1, KSC",   716,  YLW),
        ("B1087", "3",  "ACTIVE",      "SLC-40, CCAFS — VIAS",   950,  GRN),
    ]
    for i, (name, fl, status, loc, x, col) in enumerate(boosters):
        row = i // 5
        col_idx = i % 5
        bx = 24 + col_idx * 252
        by = 184 + row * 154
        children.append(booster_card(name, fl, status, loc, 0, col, bx, by, 238, 138))

    # ── Falcon Heavy section ───────────────────────────────────────
    children += [
        hrule(24, 506, 1232, LINE),
        lbl("FALCON HEAVY", 24, 522, 300, 14, sz="10px", col=GRY2, upper=True, track="3px"),
    ]
    children += [
        booster_card("B1052", "5", "ACTIVE", "LC-39A, Integration", 0, GRN, 24,  542, 290, 120),
        booster_card("B1053", "5", "ACTIVE", "LC-39A, Integration", 0, GRN, 330, 542, 290, 120),
        coord([
            lbl("FALCON HEAVY",      14, 14, 240, 20, sz="16px", col=WHT, bold=True, upper=True, track="2px"),
            lbl("SIDE CORES PAIRED", 14, 38, 240, 12, sz="9px",  col=GRY2, upper=True, track="2px"),
            hrule(14, 56, 262, LINE2),
            lbl("STATUS",  14, 68, 80,  12, sz="9px", col=GRY3, upper=True, track="2px"),
            coord([lbl("READY", 0, 0, 90, 22, sz="10px", col=GRN, align="center",
                       bold=True, track="2px", upper=True)],
                  14, 82, 90, 22, bg=BG, border=f"1px solid {GRN}", radius=1),
            lbl("NEXT",          14,  110, 80,  12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl("GOES-U · Jul 14", 104, 110, 200, 12, sz="11px", col=GRY2),
        ], 636, 542, 290, 120, bg=CARD, border=f"1px solid {LINE}", radius=1),
    ]

    # ── Starship section ──────────────────────────────────────────
    children += [
        hrule(24, 678, 1232, LINE),
        lbl("STARSHIP SYSTEM", 24, 694, 300, 14, sz="10px", col=GRY2, upper=True, track="3px"),
    ]
    children.append(coord([
        lbl("SHIP 35", 20, 14, 200, 20, sz="18px", col=WHT, bold=True, font=FM),
        lbl("STARSHIP UPPER STAGE", 20, 38, 260, 12, sz="9px", col=GRY2, upper=True, track="2px"),
        hrule(20, 56, 580-40, LINE2),
        lbl("STATUS",  20, 68,  80, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        coord([lbl("FLIGHT TEST", 0, 0, 110, 22, sz="10px", col=YLW, align="center",
                   bold=True, track="2px", upper=True)],
              20, 82, 110, 22, bg=BG, border=f"1px solid {YLW}", radius=1),
        lbl("LOCATION", 160, 68, 100, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl("Starbase, Boca Chica, TX", 160, 82, 360, 16, sz="12px", col=GRY1),
        lbl("IFT-9 PREPARATION", 20, 112, 400, 14, sz="11px", col=GRY2),
    ], 24, 714, 580, 140, bg=CARD, border=f"1px solid {LINE}", radius=1))

    children.append(coord([
        lbl("BOOSTER 14", 20, 14, 250, 20, sz="18px", col=WHT, bold=True, font=FM),
        lbl("SUPER HEAVY BOOSTER", 20, 38, 260, 12, sz="9px", col=GRY2, upper=True, track="2px"),
        hrule(20, 56, 580-40, LINE2),
        lbl("STATUS",  20, 68,  80, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        coord([lbl("STACKING", 0, 0, 110, 22, sz="10px", col=BLU2, align="center",
                   bold=True, track="2px", upper=True)],
              20, 82, 110, 22, bg=BG, border=f"1px solid {BLU2}", radius=1),
        lbl("LOCATION", 160, 68, 100, 12, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl("Starbase, Boca Chica, TX", 160, 82, 360, 16, sz="12px", col=GRY1),
        lbl("INTEGRATION IN PROGRESS", 20, 112, 400, 14, sz="11px", col=GRY2),
    ], 630, 714, 580, 140, bg=CARD, border=f"1px solid {LINE}", radius=1))

    write_view("Vehicles", children)

# ── Pads ──────────────────────────────────────────────────────────────────────
def build_pads():
    children = []
    children.append(view_embed("Components/Nav", 0, 0, 1280, 60))
    children += [
        lbl("LAUNCH COMPLEXES", 24, 84, 500, 28, sz="22px", col=WHT, bold=True, upper=True, track="4px"),
        lbl("CCAFS · VAFB · STARBASE", 24, 116, 500, 14, sz="10px", col=GRY2, upper=True, track="2px"),
        hrule(24, 144, 1232, LINE),
    ]

    pads = [
        ("LC-39A",     "LAUNCH COMPLEX 39A · KENNEDY SPACE CENTER, FL",
         "ACTIVE",     "Falcon 9 / Falcon Heavy",
         "CRS-33 · Jun 22, 2026",    GRN,   24, 160),
        ("SLC-40",     "SPACE LAUNCH COMPLEX 40 · CAPE CANAVERAL, FL",
         "ACTIVE",     "Falcon 9",
         "Starlink 10-5 · Jun 18, 2026", GRN, 660, 160),
        ("SLC-4E",     "SPACE LAUNCH COMPLEX 4E · VANDENBERG, CA",
         "ACTIVE",     "Falcon 9",
         "WorldView Legion · Jun 28, 2026", GRN, 24, 330),
        ("STARBASE",   "BOCA CHICA LAUNCH SITE · BROWNSVILLE, TX",
         "TESTING",    "Starship / Super Heavy",
         "IFT-9 · NET Q3 2026",      YLW,  660, 330),
    ]
    for name, complex_, status, vehicle, nxt, col, x, y in pads:
        children.append(pad_card(name, complex_, status, vehicle, nxt, col, x, y, 592, 150))

    # ── Global range / status ─────────────────────────────────────
    children += [
        hrule(24, 502, 1232, LINE),
        lbl("EASTERN RANGE STATUS", 24, 518, 400, 14, sz="10px", col=GRY2, upper=True, track="3px"),
    ]

    range_items = [
        ("RANGE SAFETY",     "GO",             GRN, 24),
        ("FLIGHT WEATHER",   "GO  85% Favorable", GRN, 250),
        ("TRACKING ASSETS",  "NOMINAL",        GRN, 570),
        ("RANGE CONTROL",    "MANNED",         BLU2, 840),
        ("DOWNRANGE SHIPS",  "ON STATION",     GRN, 1070),
    ]
    for title, val, col, x in range_items:
        children.append(coord([
            lbl(title, 12, 10, 200, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl(val,   12, 26, 200, 18, sz="13px", col=col, bold=True),
        ], x, 538, 210, 52, bg=CARD, border=f"1px solid {LINE}", radius=1))

    # ── Pad cameras / view links ──────────────────────────────────
    children += [
        hrule(24, 610, 1232, LINE),
        lbl("PAD CAMERA FEEDS", 24, 626, 300, 14, sz="10px", col=GRY2, upper=True, track="3px"),
    ]
    cams = ["LC-39A PAD", "SLC-40 PAD", "SLC-40 FLAME TRENCH", "STARBASE OLM"]
    for i, cam in enumerate(cams):
        cx = 24 + i * 308
        children.append(coord([
            lbl(cam, 0, 0, 280, 40, sz="10px", col=GRY3, align="center",
                upper=True, track="2px"),
            lbl("FEED UNAVAILABLE", 0, 40, 280, 60, sz="11px",
                col=GRY3, align="center"),
        ], cx, 646, 282, 110, bg=CARD, border=f"1px solid {LINE}", radius=1))

    write_view("Pads", children)

# ── Fleet ─────────────────────────────────────────────────────────────────────
def build_fleet():
    children = []
    children.append(view_embed("Components/Nav", 0, 0, 1280, 60))
    children += [
        lbl("FLEET STATUS", 24, 84, 400, 28, sz="22px", col=WHT, bold=True, upper=True, track="4px"),
        lbl("RECOVERY VESSELS · SUPPORT SHIPS", 24, 116, 500, 14, sz="10px", col=GRY2, upper=True, track="2px"),
        hrule(24, 144, 1232, LINE),
        lbl("AUTONOMOUS SPACEPORT DRONE SHIPS", 24, 160, 500, 14, sz="10px", col=GRY2, upper=True, track="3px"),
    ]

    asds = [
        ("OCISLY",   "AUTONOMOUS SPACEPORT DRONE SHIP",
         "DEPLOYED",  "Atlantic · 28.5° Inclination",
         "Starlink 10-5",   GRN,   24, 180, 390, 160),
        ("JRTI",     "AUTONOMOUS SPACEPORT DRONE SHIP",
         "DEPLOYED",  "Pacific · SLC-4E Downrange",
         "WorldView Legion", GRN,  440, 180, 390, 160),
        ("NUSQUAM",  "AUTONOMOUS SPACEPORT DRONE SHIP",
         "TRANSIT",   "Gulf of Mexico — Starbase",
         "IFT-9 Prep",      YLW,  856, 180, 390, 160),
    ]
    for name, type_, status, loc, mission, col, x, y, w, h in asds:
        children.append(coord([
            lbl(name,   14, 14, w-28, 22, sz="16px", col=WHT, bold=True, upper=True, track="2px"),
            lbl(type_,  14, 38, w-28, 12, sz="9px",  col=GRY2, upper=True, track="2px"),
            hrule(14, 56, w-28, LINE2),
            lbl("STATUS",   14, 66, 70,  12, sz="9px", col=GRY3, upper=True, track="2px"),
            coord([lbl(status, 0, 0, 100, 24, sz="10px", col=col, align="center",
                       bold=True, track="2px", upper=True)],
                  14, 80, 100, 24, bg=BG, border=f"1px solid {col}", radius=1),
            lbl("LOCATION", 14, 112, 70, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl(loc,        14, 126, w-28, 14, sz="11px", col=GRY1),
            lbl("ASSIGNED",  14, 144, 70, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl(mission,     14, 144, w-28, 14, sz="11px", col=GRY2),
        ], x, y, w, h, bg=CARD, border=f"1px solid {LINE}", radius=1))

    # ── Fairing recovery ──────────────────────────────────────────
    children += [
        hrule(24, 358, 1232, LINE),
        lbl("FAIRING RECOVERY VESSELS", 24, 374, 400, 14, sz="10px", col=GRY2, upper=True, track="3px"),
        coord([
            lbl("GO MS. CHIEF", 14, 14, 300, 20, sz="14px", col=WHT, bold=True, upper=True, track="1px"),
            lbl("FAIRING RECOVERY VESSEL", 14, 36, 300, 12, sz="9px", col=GRY2, upper=True, track="2px"),
            hrule(14, 54, 560, LINE2),
            lbl("STATUS",   14, 64, 70, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            coord([lbl("ON STATION", 0, 0, 110, 24, sz="10px", col=GRN, align="center",
                       bold=True, track="2px", upper=True)],
                  14, 78, 110, 24, bg=BG, border=f"1px solid {GRN}", radius=1),
            lbl("LOCATION", 160, 64, 100, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl("Atlantic Recovery Zone · 28.5°", 160, 78, 350, 16, sz="12px", col=GRY1),
            lbl("MISSION", 14, 110, 100, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl("Starlink 10-5 Fairing Half Recovery", 14, 124, 500, 14, sz="11px", col=GRY2),
        ], 24, 394, 590, 148, bg=CARD, border=f"1px solid {LINE}", radius=1),
        coord([
            lbl("GO MS. TREE",  14, 14, 300, 20, sz="14px", col=WHT, bold=True, upper=True, track="1px"),
            lbl("FAIRING RECOVERY VESSEL", 14, 36, 300, 12, sz="9px", col=GRY2, upper=True, track="2px"),
            hrule(14, 54, 560, LINE2),
            lbl("STATUS",   14, 64, 70, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            coord([lbl("TRANSIT", 0, 0, 110, 24, sz="10px", col=YLW, align="center",
                       bold=True, track="2px", upper=True)],
                  14, 78, 110, 24, bg=BG, border=f"1px solid {YLW}", radius=1),
            lbl("LOCATION", 160, 64, 100, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl("Port Canaveral → CCAFS", 160, 78, 350, 16, sz="12px", col=GRY1),
            lbl("MISSION", 14, 110, 100, 12, sz="9px", col=GRY3, upper=True, track="2px"),
            lbl("Returning from WorldView Legion recovery", 14, 124, 500, 14, sz="11px", col=GRY2),
        ], 640, 394, 590, 148, bg=CARD, border=f"1px solid {LINE}", radius=1),
    ]

    # ── Support ships ─────────────────────────────────────────────
    children += [
        hrule(24, 556, 1232, LINE),
        lbl("SUPPORT VESSELS", 24, 572, 300, 14, sz="10px", col=GRY2, upper=True, track="3px"),
    ]
    support = [
        ("GO NAVIGATOR",    "Support / Tug",         "ACTIVE",  "Port Canaveral, FL",  GRN,  24,   592),
        ("GO SEARCHER",     "Crew & Cargo Recovery",  "ACTIVE",  "Atlantic Recovery Zone", GRN, 334, 592),
        ("GO QUEST",        "Crew Recovery",          "STANDBY", "Port Canaveral, FL",  GRY2, 644, 592),
        ("NRC CYGNUS",      "Offshore Supply",        "TRANSIT", "Gulf of Mexico",      YLW,  954, 592),
    ]
    for name, type_, status, loc, col, x, y in support:
        children.append(coord([
            lbl(name,  12, 12, 280, 18, sz="13px", col=WHT, bold=True, upper=True, track="1px"),
            lbl(type_, 12, 32, 280, 12, sz="9px",  col=GRY2, upper=True, track="2px"),
            hrule(12, 50, 275, LINE2),
            coord([lbl(status, 0, 0, 100, 22, sz="10px", col=col, align="center",
                       bold=True, track="2px", upper=True)],
                  12, 62, 100, 22, bg=BG, border=f"1px solid {col}", radius=1),
            lbl(loc, 12, 92, 280, 14, sz="10px", col=GRY2),
        ], x, y, 296, 116, bg=CARD, border=f"1px solid {LINE}", radius=1))

    write_view("Fleet", children)

# ── Alarms / Events ──────────────────────────────────────────────────────────
def build_events():
    children = []
    children.append(view_embed("Components/Nav", 0, 0, 1280, 60))
    children += [
        lbl("EVENTS & ALERTS", 24, 84, 400, 28, sz="22px", col=WHT, bold=True, upper=True, track="4px"),
        lbl("SYSTEM · WEATHER · RANGE · ANOMALIES", 24, 116, 500, 14, sz="10px", col=GRY2, upper=True, track="2px"),
        hrule(24, 144, 1232, LINE),
    ]

    # Header
    children.append(coord([
        lbl("TIME (UTC)",   16,  0, 120, 24, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl("LEVEL",       148,  0,  80, 24, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl("SOURCE",      240,  0, 120, 24, sz="9px", col=GRY3, upper=True, track="2px"),
        lbl("EVENT",       376,  0, 800, 24, sz="9px", col=GRY3, upper=True, track="2px"),
    ], 24, 158, 1232, 24, bg=BG))

    events = [
        ("14:31:07", "HIGH",    GRN,   "STARLINK 10-5", "Vehicle encapsulation complete — fairing closeout nominal"),
        ("14:22:44", "INFO",    BLU2,  "RANGE",         "Eastern Range GO for launch on Jun 18 window"),
        ("13:58:12", "INFO",    BLU2,  "WEATHER",       "Launch weather: 85% favorable — acceptable winds at 250mb"),
        ("13:40:00", "CAUTION", YLW,   "CRS-33",        "Payload power-on delayed 2h — troubleshooting IMU heater"),
        ("12:30:00", "INFO",    BLU2,  "OCISLY",        "Drone ship OCISLY departed Port Canaveral — on station by T-6h"),
        ("11:14:28", "INFO",    BLU2,  "SLC-40",        "Flame deflector water system test complete — NOMINAL"),
        ("10:02:05", "INFO",    BLU2,  "B1073",         "Booster B1073.8 propellant loading simulation complete"),
        ("09:30:00", "CAUTION", YLW,   "STARBASE",      "IFT-9 booster 14 stacking paused — GSE inspection"),
        ("08:15:52", "INFO",    BLU2,  "CREW-11",       "Crew medical checks complete — crew GO for launch"),
        ("07:44:11", "CLEAR",   GRN,   "WEATHER",       "GOES observation: no upper level wind anomalies"),
        ("06:20:00", "INFO",    BLU2,  "FLEET",         "GO Searcher departed Port Canaveral for recovery station"),
        ("05:11:38", "HIGH",    RED,   "CREW-11",       "SCRUB: LC-39A ground support equipment fault — recycling 24h"),
    ]

    lv_cols = {"HIGH": GRN, "INFO": BLU2, "CAUTION": YLW, "CLEAR": GRN, "SCRUB": RED}

    for i, (t, lvl, col, src, msg) in enumerate(events):
        y = 186 + i * 40
        lv_c = {RED:"CRIT", YLW:"WARN", GRN:"OK", BLU2:"INFO"}.get(col, "INFO")
        children.append(coord([
            lbl(t,   16,  0, 120, 38, sz="11px", col=GRY2, font=FM),
            coord([lbl(lv_c, 0, 0, 76, 24, sz="9px", col=col, align="center",
                       bold=True, track="2px", upper=True)],
                  148, 7, 76, 24, bg=BG, border=f"1px solid {col}", radius=1),
            lbl(src, 240,  0, 120, 38, sz="10px", col=GRY2, upper=True, track="1px"),
            lbl(msg, 376,  0, 840, 38, sz="12px", col=WHT if col != GRY2 else GRY1),
            hrule(0, 39, 1232, LINE),
        ], 24, y, 1232, 40, bg=BG))

    write_view("Events", children)

# ═══════════════════════════════════════════════════════════════════════════════
#  PROJECT FILES
# ═══════════════════════════════════════════════════════════════════════════════
def write_project():
    write("project.json", {
        "title": "launch", "description": "Launch Operations Control — SpaceX Style",
        "parent": "", "enabled": True, "inheritable": False
    })
    pc = {
        "pages": {
            "/":          {"title": "Overview",       "viewPath": "Overview"},
            "/launches":  {"title": "Launch Manifest","viewPath": "Launches"},
            "/vehicles":  {"title": "Vehicle Status", "viewPath": "Vehicles"},
            "/pads":      {"title": "Launch Pads",    "viewPath": "Pads"},
            "/fleet":     {"title": "Fleet Status",   "viewPath": "Fleet"},
            "/events":    {"title": "Events",         "viewPath": "Events"},
        },
        "sharedDocks": {"cornerPriority": "top-bottom", "bottom": [], "left": [], "right": []}
    }
    write("com.inductiveautomation.perspective/page-config/config.json", pc)
    write("com.inductiveautomation.perspective/page-config/resource.json",
          resource(["config.json"]))
    print("  wrote project.json + page-config")

# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD + DEPLOY
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Building launch-ops project...")
    write_project()
    build_nav()
    build_overview()
    build_launches()
    build_vehicles()
    build_pads()
    build_fleet()
    build_events()

    print(f"\nDeploying to {DEST}...")
    if os.path.exists(DEST):
        shutil.rmtree(DEST)
    subprocess.run([
        "rsync", "-a",
        "--exclude=.git", "--exclude=*.py", "--exclude=tags",
        f"{SRC}/", f"{DEST}/"
    ], check=True)
    subprocess.run(["find", DEST, "-name", "*.json", "-exec", "touch", "{}", ";"])
    print("Done. Restart Ignition gateway to pick up new project.")
