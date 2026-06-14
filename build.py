#!/usr/bin/env python3
"""
Build launch-ops Ignition Perspective project — SpaceX style.
Layout guide: flex-first, explicit grow/shrink/basis, rem sizing, working nav events.
"""
import json, os, shutil, subprocess

SRC  = os.path.dirname(os.path.abspath(__file__))
DEST = "/usr/local/ignition/data/projects/launch"

# ── Palette ───────────────────────────────────────────────────────────────────
BG   = "#000000"
DARK = "#080808"
CARD = "#0D0D0D"
LINE = "#1A1A1A"
LINE2= "#252525"
WHT  = "#FFFFFF"
GRY1 = "#AAAAAA"
GRY2 = "#666666"
GRY3 = "#2E2E2E"
GRN  = "#00D4AA"
YLW  = "#FFB300"
RED  = "#FF3B3B"
ORG  = "#FF6B00"
BLU  = "#1A90FF"

F  = "D-DIN, 'Barlow', 'Helvetica Neue', Arial, sans-serif"
FM = "'D-DIN Exp', 'Share Tech Mono', 'Courier New', monospace"

# ── Core helpers ──────────────────────────────────────────────────────────────

def _pos(grow=None, shrink=None, basis=None):
    d = {}
    if grow   is not None: d["grow"]   = grow
    if shrink is not None: d["shrink"] = shrink
    if basis  is not None:
        d["basis"] = basis
    elif grow is not None or shrink is not None:
        d["basis"] = "auto"  # guide: all three required; auto = fixed-size default
    return d

def flex(children, direction="column", justify="flex-start", align="stretch",
         grow=None, shrink=None, basis=None, gap=None, pad=None,
         bg=None, border=None, radius=None, wrap=None, name="flex",
         min_height=None, **kw_style):
    style = {}
    if gap:        style["gap"]             = gap
    if pad:        style["padding"]         = pad
    if bg:         style["backgroundColor"] = bg
    if border:     style["border"]          = border
    if radius:     style["borderRadius"]    = radius
    if min_height: style["minHeight"]       = min_height
    style.update(kw_style)
    props = {"direction": direction, "justify": justify,
             "alignItems": align, "style": style}
    if wrap: props["wrap"] = wrap
    comp = {"type": "ia.container.flex", "meta": {"name": name},
            "props": props, "children": children}
    pos = _pos(grow, shrink, basis)
    if pos: comp["position"] = pos
    return comp

def lbl(text, sz="0.875rem", col=WHT, bold=False, track="normal", upper=False,
        align="left", font=F, grow=None, shrink=None, basis=None, name="lbl",
        min_width=None, **kw_style):
    style = {"color": col, "fontSize": sz, "fontFamily": font,
             "textAlign": align, "letterSpacing": track}
    if bold:  style["fontWeight"]    = "700"
    if upper: style["textTransform"] = "uppercase"
    if min_width: style["minWidth"]  = min_width
    style.update(kw_style)
    comp = {"type": "ia.display.label", "meta": {"name": name},
            "props": {"text": text, "style": style}}
    pos = _pos(grow, shrink, basis)
    if pos: comp["position"] = pos
    return comp

def btn(text, page=None, view_path=None, bg="rgba(255,255,255,0.06)",
        col=WHT, border="1px solid #2E2E2E", sz="0.6875rem",
        radius="1px", track="2px", grow=0, shrink=0, basis="auto",
        min_width=None, name="btn"):
    style = {"backgroundColor": bg, "color": col, "fontSize": sz,
             "fontFamily": F, "letterSpacing": track,
             "textTransform": "uppercase", "border": border,
             "borderRadius": radius, "cursor": "pointer",
             "padding": "0.5rem 1.25rem", "whiteSpace": "nowrap"}
    if min_width: style["minWidth"] = min_width
    if page:      script = f"system.perspective.navigate(page='{page}')"
    elif view_path: script = f"system.perspective.navigate(view='{view_path}')"
    else:         script = ""
    comp = {"type": "ia.input.button", "meta": {"name": name},
            "props": {"text": text, "style": style},
            "position": _pos(grow, shrink, basis)}
    if script:
        comp["events"] = {"component": {"onActionPerformed": {
            "type": "script", "scope": "G",
            "config": {"script": script}
        }}}
    return comp

def spacer(grow=1):
    return {"type": "ia.display.label", "meta": {"name": "spacer"},
            "props": {"text": "", "style": {}},
            "position": _pos(grow=grow, shrink=1, basis="0%")}

def hrule(col=LINE):
    return lbl("", grow=0, shrink=0, basis="1px",
               backgroundColor=col, display="block")

def vrule(col=LINE2, width="1px"):
    return lbl("", grow=0, shrink=0, basis=width,
               alignSelf="stretch", backgroundColor=col)

def dot_status(col=GRN, text="NOMINAL"):
    return flex([
        lbl("●", sz="0.5rem", col=col, grow=0, shrink=0),
        lbl(text, sz="0.625rem", col=col, upper=True, track="2px",
            grow=0, shrink=0),
    ], direction="row", align="center", gap="0.375rem",
       grow=0, shrink=0, basis="auto")

def status_badge(label, col):
    return flex([
        lbl(label, sz="0.625rem", col=col, bold=True, track="2px",
            upper=True, align="center")
    ], direction="row", justify="center", align="center",
       grow=0, shrink=0, basis="auto",
       pad="0.25rem 0.75rem",
       border=f"1px solid {col}", radius="1px")

def embed_view(path, grow=0, shrink=0, basis="auto"):
    comp = {"type": "ia.display.view", "meta": {"name": "embed"},
            "props": {"path": path, "style": {}},
            "position": _pos(grow, shrink, basis)}
    return comp

def kpi_card(title, value, sub, col, grow=1, shrink=1):
    return flex([
        lbl(title, sz="0.625rem", col=GRY2, upper=True, track="2px",
            grow=0, shrink=0),
        lbl(value, sz="2rem", col=col, bold=True, font=FM,
            grow=0, shrink=0),
        lbl(sub,   sz="0.6875rem", col=GRY2, grow=0, shrink=0),
    ], direction="column", gap="0.375rem",
       grow=grow, shrink=shrink, basis="0%",
       bg=CARD, pad="1rem 1.25rem",
       border=f"1px solid {LINE}", radius="1px")

def section_header(title):
    return lbl(title, sz="0.625rem", col=GRY2, upper=True, track="3px",
               grow=0, shrink=0)

def table_header(*cols_widths):
    children = []
    for c, b in cols_widths:
        children.append(lbl(c, sz="0.5625rem", col=GRY3, upper=True,
                            track="2px", grow=1 if b == "*" else 0,
                            shrink=1 if b == "*" else 0,
                            basis="0%" if b == "*" else b))
    return flex(children, direction="row", align="center", gap="0.75rem",
                grow=0, shrink=0, pad="0.375rem 0.75rem")

def launch_row(mission, vehicle, site, date, col):
    badge = {GRN:"GO", YLW:"HOLD", ORG:"TBD", RED:"SCRUB"}.get(col, "GO")
    return flex([
        lbl(mission, sz="0.8125rem", col=WHT, grow=2, shrink=1, basis="0%"),
        lbl(vehicle, sz="0.6875rem", col=GRY1, upper=True, track="1px",
            grow=1, shrink=1, basis="0%"),
        lbl(site,    sz="0.6875rem", col=GRY1, upper=True, track="1px",
            grow=1, shrink=1, basis="0%"),
        lbl(date,    sz="0.6875rem", col=GRY2,
            grow=1, shrink=1, basis="0%"),
        status_badge(badge, col),
    ], direction="row", align="center", gap="0.75rem",
       grow=0, shrink=0, basis="auto",
       pad="0.625rem 0.75rem",
       borderBottom=f"1px solid {LINE}")

def booster_card(name, flights, status, loc, col, grow=1, shrink=1):
    return flex([
        flex([
            lbl(name,    sz="1rem",   col=WHT, bold=True, font=FM,
                grow=1, shrink=1, basis="0%"),
            lbl(f"FLT {flights}", sz="0.625rem", col=GRY2, upper=True,
                track="2px", grow=0, shrink=0),
        ], direction="row", align="center", gap="0.5rem",
           grow=0, shrink=0),
        hrule(LINE2),
        lbl("STATUS",   sz="0.5625rem", col=GRY3, upper=True, track="2px",
            grow=0, shrink=0),
        lbl(status,     sz="0.75rem",   col=col, upper=True, track="1px",
            grow=0, shrink=0),
        lbl("LOCATION", sz="0.5625rem", col=GRY3, upper=True, track="2px",
            grow=0, shrink=0),
        lbl(loc,        sz="0.6875rem", col=GRY2, grow=0, shrink=0),
    ], direction="column", gap="0.375rem",
       grow=grow, shrink=shrink, basis="0%",
       bg=CARD, pad="1rem",
       border=f"1px solid {LINE}", radius="1px")

def pad_card(name, site, status, vehicle, nxt, col, grow=1, shrink=1):
    return flex([
        flex([
            lbl(name,   sz="1.25rem", col=WHT, bold=True, upper=True, track="3px",
                grow=1, shrink=1, basis="0%"),
            status_badge(status, col),
        ], direction="row", align="center", gap="0.75rem",
           grow=0, shrink=0),
        lbl(site, sz="0.625rem", col=GRY2, upper=True, track="2px",
            grow=0, shrink=0),
        hrule(LINE2),
        flex([
            flex([
                lbl("VEHICLE", sz="0.5rem", col=GRY3, upper=True, track="2px",
                    grow=0, shrink=0),
                lbl(vehicle, sz="0.75rem", col=GRY1, grow=0, shrink=0),
            ], direction="column", gap="0.25rem", grow=1, shrink=1, basis="0%"),
            flex([
                lbl("NEXT LAUNCH", sz="0.5rem", col=GRY3, upper=True, track="2px",
                    grow=0, shrink=0),
                lbl(nxt, sz="0.75rem", col=GRY2, grow=0, shrink=0),
            ], direction="column", gap="0.25rem", grow=1, shrink=1, basis="0%"),
        ], direction="row", gap="1rem", grow=0, shrink=0),
    ], direction="column", gap="0.5rem",
       grow=grow, shrink=shrink, basis="0%",
       bg=CARD, pad="1.25rem",
       border=f"1px solid {LINE}", radius="1px")

# ── resource.json helper ──────────────────────────────────────────────────────
def resource(files):
    return {"scope": "G", "version": 1, "restricted": False, "overridable": True,
            "files": files,
            "attributes": {"lastModification": {
                "actor": "admin", "timestamp": "2026-06-13T00:00:00Z"}}}

# ── Write helpers ─────────────────────────────────────────────────────────────
def write(rel, obj):
    full = os.path.join(SRC, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def view_json(root_comp, width=1280, height=900):
    return {"custom": {}, "params": {},
            "props": {"defaultSize": {"width": width, "height": height}},
            "root": root_comp}

def write_view(name, root_comp, width=1280, height=900):
    base = f"com.inductiveautomation.perspective/views/{name}"
    write(f"{base}/view.json",     view_json(root_comp, width, height))
    write(f"{base}/resource.json", resource(["view.json"]))
    print(f"  {name}")

# ═══════════════════════════════════════════════════════════════════════════════
#  SHARED NAV COMPONENT
# ═══════════════════════════════════════════════════════════════════════════════
def build_nav():
    PAGES = [
        ("Overview",  "/"),
        ("Launches",  "/launches"),
        ("Vehicles",  "/vehicles"),
        ("Pads",      "/pads"),
        ("Fleet",     "/fleet"),
        ("Events",    "/events"),
    ]
    nav_btns = [
        btn(label, page=page,
            bg="transparent", border="none",
            col=GRY1, sz="0.6875rem", track="1px",
            grow=0, shrink=0, basis="auto", name=f"nav_{label}")
        for label, page in PAGES
    ]

    root = flex([
        # Logo
        lbl("✦  LAUNCH OPS", sz="0.8125rem", col=WHT, bold=True,
            track="3px", upper=True, grow=0, shrink=0),
        vrule(),
        # Nav links
        flex(nav_btns, direction="row", gap="0.125rem",
             grow=0, shrink=0, basis="auto"),
        # Spacer
        spacer(),
        # Status
        dot_status(GRN, "NOMINAL"),
    ], direction="row", align="center", gap="1rem",
       bg=BG, pad="0 1.25rem",
       borderBottom=f"1px solid {LINE2}", min_height="56px",
       name="NavRoot")

    write_view("Components/Nav", root, height=56)

# ═══════════════════════════════════════════════════════════════════════════════
#  OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
def build_overview():
    LAUNCHES = [
        ("Starlink Group 10-5",            "Falcon 9",       "SLC-40, CCAFS",  "Jun 18, 2026", GRN),
        ("CRS-33 (SpX-33)",                "Falcon 9",       "LC-39A, KSC",    "Jun 22, 2026", GRN),
        ("Maxar WorldView Legion 3-4",     "Falcon 9",       "SLC-4E, VAFB",   "Jun 28, 2026", GRN),
        ("Crew-11",                        "Falcon 9",       "LC-39A, KSC",    "Jul 03, 2026", YLW),
        ("Starlink Group 11-1",            "Falcon 9",       "SLC-40, CCAFS",  "Jul 09, 2026", GRN),
        ("GOES-U",                         "Falcon Heavy",   "LC-39A, KSC",    "Jul 14, 2026", ORG),
    ]

    # ── Hero countdown ────────────────────────────────────────────
    hero = flex([
        lbl("NEXT LAUNCH", sz="0.625rem", col=GRY2, upper=True, track="4px",
            align="center", grow=0, shrink=0),
        lbl("T−  00 : 04 : 22 : 17", sz="4.5rem", col=WHT, bold=True,
            font=FM, track="4px", align="center", grow=0, shrink=0),
        lbl("FALCON 9  ·  STARLINK GROUP 10-5  ·  SLC-40, CAPE CANAVERAL",
            sz="0.8125rem", col=GRY1, upper=True, track="2px",
            align="center", grow=0, shrink=0),
        lbl("NET: JUN 18, 2026  ·  21:45 UTC  ·  WINDOW: INSTANTANEOUS",
            sz="0.6875rem", col=GRY2, track="1px",
            align="center", grow=0, shrink=0),
        flex([
            btn("WATCH LIVE",      page="/",         grow=0, shrink=0),
            btn("MISSION DETAILS", page="/launches",
                bg="transparent", col=GRY2, border=f"1px solid {LINE2}",
                grow=0, shrink=0),
        ], direction="row", justify="center", gap="0.75rem",
           grow=0, shrink=0),
    ], direction="column", justify="center", align="center", gap="0.75rem",
       grow=0, shrink=0, bg=DARK, pad="2.5rem 1rem",
       borderBottom=f"1px solid {LINE}")

    # ── KPI strip ─────────────────────────────────────────────────
    kpi_strip = flex([
        kpi_card("TOTAL FLOW RATE",    "244 L/min",   "FI-101 + FI-102 combined", BLU),
        kpi_card("ACTIVE MISSIONS",    "7",           "4 Starlink · 2 Commercial · 1 Gov", GRN),
        kpi_card("FLEET SHIPS",        "6",           "2 ASDS · 4 Support vessels", WHT),
        kpi_card("LAUNCHES THIS YEAR", "42",          "38 Falcon 9  ·  4 Falcon Heavy", YLW),
    ], direction="row", gap="0.75rem",
       grow=0, shrink=0, wrap="wrap")

    # ── Launch manifest table ─────────────────────────────────────
    hdr = table_header(
        ("MISSION",  "*"), ("VEHICLE", "140px"), ("SITE", "160px"),
        ("DATE",     "140px"), ("STATUS", "80px"),
    )
    rows = [launch_row(m, v, s, d, c) for m, v, s, d, c in LAUNCHES]

    manifest = flex(
        [section_header("UPCOMING LAUNCHES"),
         flex([hdr] + rows, direction="column", gap="0",
              grow=1, shrink=1, basis="0%",
              bg=CARD, border=f"1px solid {LINE}", radius="1px",
              overflow="hidden"),
        ],
        direction="column", gap="0.75rem",
        grow=1, shrink=1, basis="0%"
    )

    # ── Page root ─────────────────────────────────────────────────
    root = flex([
        embed_view("Components/Nav", grow=0, shrink=0, basis="56px"),
        hero,
        kpi_strip,
        manifest,
    ], direction="column", gap="1rem", bg=BG, pad="0 0 1rem 0",
       name="OverviewRoot")

    write_view("Overview", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  LAUNCHES
# ═══════════════════════════════════════════════════════════════════════════════
def build_launches():
    missions = [
        ("Starlink Group 10-5",       "Falcon 9 B1073.8",   "SLC-40",  "Jun 18", "21:45 UTC", GRN,
         "Booster recovery: OCISLY",   "50th Starlink launch of 2026"),
        ("CRS-33",                    "Falcon 9 B1087.3",   "LC-39A",  "Jun 22", "14:30 UTC", GRN,
         "Booster recovery: LZ-1",     "ISS cargo resupply"),
        ("WorldView Legion 3-4",      "Falcon 9 B1060.18",  "SLC-4E",  "Jun 28", "09:15 UTC", GRN,
         "Booster recovery: JRTI",     "Earth imaging constellation"),
        ("Crew-11",                   "Falcon 9 B1077.4",   "LC-39A",  "Jul 03", "16:00 UTC", YLW,
         "Booster recovery: LZ-1",     "4-person ISS crew rotation"),
        ("Starlink Group 11-1",       "Falcon 9 B1058.19",  "SLC-40",  "Jul 09", "03:20 UTC", GRN,
         "Booster recovery: OCISLY",   "V2 Mini satellites"),
        ("GOES-U",                    "Falcon Heavy",        "LC-39A",  "Jul 14", "11:00 UTC", ORG,
         "Side core recovery: LZ-1/2", "NOAA geostationary weather"),
        ("Starlink Group 10-7",       "Falcon 9 B1062.16",  "SLC-40",  "Jul 19", "02:45 UTC", ORG,
         "TBD",                        ""),
        ("Polaris Dawn STS-1",        "Falcon 9 B1091.1",   "LC-39A",  "Aug 04", "TBD",       ORG,
         "Booster recovery: LZ-1",     "Private spacewalk mission"),
    ]

    def mission_card(name, vehicle, site, date, time_, col, note, sub):
        badge = {GRN:"GO", YLW:"HOLD", ORG:"TBD", RED:"SCRUB"}.get(col, "GO")
        return flex([
            # Left accent bar
            flex([], direction="column", grow=0, shrink=0, basis="3px",
                 backgroundColor=col, alignSelf="stretch"),
            # Content
            flex([
                # Top row: name + badge
                flex([
                    lbl(name, sz="0.9375rem", col=WHT, bold=True,
                        grow=1, shrink=1, basis="0%"),
                    status_badge(badge, col),
                ], direction="row", align="center", gap="1rem",
                   grow=0, shrink=0),
                lbl(sub,  sz="0.6875rem", col=GRY2, grow=0, shrink=0)
                    if sub else lbl("", sz="0", col=BG, grow=0, shrink=0),
                lbl(note, sz="0.6875rem", col=GRY3, grow=0, shrink=0),
                # Details row
                flex([
                    flex([
                        lbl("VEHICLE", sz="0.5rem", col=GRY3, upper=True, track="2px",
                            grow=0, shrink=0),
                        lbl(vehicle,   sz="0.75rem", col=GRY1, grow=0, shrink=0),
                    ], direction="column", gap="0.25rem", grow=1, shrink=1, basis="0%"),
                    flex([
                        lbl("SITE",  sz="0.5rem", col=GRY3, upper=True, track="2px",
                            grow=0, shrink=0),
                        lbl(site,    sz="0.75rem", col=GRY1, grow=0, shrink=0),
                    ], direction="column", gap="0.25rem", grow=1, shrink=1, basis="0%"),
                    flex([
                        lbl("DATE",  sz="0.5rem", col=GRY3, upper=True, track="2px",
                            grow=0, shrink=0),
                        lbl(f"{date}  ·  {time_}", sz="1rem", col=WHT,
                            bold=True, font=FM, grow=0, shrink=0),
                    ], direction="column", gap="0.25rem", grow=1, shrink=1, basis="0%"),
                ], direction="row", gap="1.5rem", grow=0, shrink=0,
                   marginTop="0.25rem"),
            ], direction="column", gap="0.375rem",
               grow=1, shrink=1, basis="0%", pad="1rem"),
        ], direction="row", align="stretch",
           grow=0, shrink=0, bg=CARD,
           border=f"1px solid {LINE}", radius="1px", overflow="hidden")

    cards = [mission_card(*m) for m in missions]

    root = flex([
        embed_view("Components/Nav", grow=0, shrink=0, basis="56px"),
        flex([
            flex([
                lbl("LAUNCH MANIFEST", sz="1.375rem", col=WHT,
                    bold=True, upper=True, track="4px",
                    grow=1, shrink=1, basis="0%"),
                lbl("2026  ·  MANIFEST SUBJECT TO CHANGE",
                    sz="0.625rem", col=GRY2, upper=True, track="2px",
                    grow=0, shrink=0),
            ], direction="column", gap="0.25rem", grow=0, shrink=0),
            *cards,
        ], direction="column", gap="0.5rem",
           grow=1, shrink=1, basis="0%",
           pad="1.25rem", overflow="auto"),
    ], direction="column", bg=BG, name="LaunchesRoot")

    write_view("Launches", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  VEHICLES
# ═══════════════════════════════════════════════════════════════════════════════
def build_vehicles():
    f9_boosters = [
        ("B1058", "19", "ACTIVE",       "JRTI — At Sea",           GRN),
        ("B1060", "18", "ACTIVE",       "OCISLY — Port Canaveral", GRN),
        ("B1061", "15", "REFURBISHING", "SpaceX Hangar 2, KSC",    YLW),
        ("B1062", "16", "ACTIVE",       "SLC-40, CCAFS",           GRN),
        ("B1067", "14", "ACTIVE",       "SLC-4E, Vandenberg",      GRN),
        ("B1071", "12", "STANDBY",      "SpaceX Hangar, CCAFS",    GRY2),
        ("B1073", "8",  "ACTIVE",       "En route to OCISLY",      GRN),
        ("B1077", "4",  "ACTIVE",       "LC-39A Integration",      GRN),
        ("B1085", "3",  "REFURBISHING", "SpaceX Hangar 1, KSC",    YLW),
        ("B1087", "3",  "ACTIVE",       "SLC-40, CCAFS — VIAS",    GRN),
    ]

    def starship_card(vehicle, role, status, col, location, note):
        return flex([
            flex([
                lbl(vehicle, sz="1.125rem", col=WHT, bold=True, font=FM,
                    grow=1, shrink=1, basis="0%"),
                status_badge(status, col),
            ], direction="row", align="center", gap="1rem", grow=0, shrink=0),
            lbl(role, sz="0.625rem", col=GRY2, upper=True, track="2px",
                grow=0, shrink=0),
            flex([], direction="row", grow=0, shrink=0, basis="1px",
                 backgroundColor=LINE2, alignSelf="stretch"),
            flex([
                flex([lbl("LOCATION", sz="0.5rem", col=GRY3, upper=True, track="2px",
                          grow=0, shrink=0),
                      lbl(location, sz="0.8125rem", col=GRY1, grow=0, shrink=0)],
                     direction="column", gap="0.25rem", grow=1, shrink=1, basis="0%"),
                flex([lbl("NOTES", sz="0.5rem", col=GRY3, upper=True, track="2px",
                          grow=0, shrink=0),
                      lbl(note, sz="0.75rem", col=GRY2, grow=0, shrink=0)],
                     direction="column", gap="0.25rem", grow=1, shrink=1, basis="0%"),
            ], direction="row", gap="1rem", grow=0, shrink=0),
        ], direction="column", gap="0.5rem",
           grow=1, shrink=1, basis="0%",
           bg=CARD, pad="1.25rem",
           border=f"1px solid {LINE}", radius="1px")

    root = flex([
        embed_view("Components/Nav", grow=0, shrink=0, basis="56px"),
        flex([
            # Header
            lbl("VEHICLE STATUS", sz="1.375rem", col=WHT,
                bold=True, upper=True, track="4px", grow=0, shrink=0),
            lbl("FALCON 9  ·  FALCON HEAVY  ·  STARSHIP",
                sz="0.625rem", col=GRY2, upper=True, track="2px",
                grow=0, shrink=0),
            # F9 section
            section_header("FALCON 9 BOOSTER FLEET"),
            flex([booster_card(n, f, s, l, c)
                  for n, f, s, l, c in f9_boosters],
                 direction="row", gap="0.5rem", wrap="wrap",
                 grow=0, shrink=0),
            # Falcon Heavy section
            section_header("FALCON HEAVY"),
            flex([
                booster_card("B1052", "5", "ACTIVE", "LC-39A, Integration", GRN),
                booster_card("B1053", "5", "ACTIVE", "LC-39A, Integration", GRN),
                flex([
                    lbl("FALCON HEAVY", sz="1rem", col=WHT, bold=True, upper=True,
                        track="2px", grow=0, shrink=0),
                    lbl("SIDE CORES PAIRED", sz="0.625rem", col=GRY2, upper=True,
                        track="2px", grow=0, shrink=0),
                    status_badge("READY", GRN),
                    flex([
                        lbl("NEXT", sz="0.5rem", col=GRY3, upper=True, track="2px",
                            grow=0, shrink=0),
                        lbl("GOES-U · Jul 14", sz="0.8125rem", col=GRY2,
                            grow=0, shrink=0),
                    ], direction="column", gap="0.25rem", grow=0, shrink=0),
                ], direction="column", gap="0.5rem",
                   grow=1, shrink=1, basis="0%",
                   bg=CARD, pad="1.25rem",
                   border=f"1px solid {LINE}", radius="1px"),
            ], direction="row", gap="0.5rem",
               grow=0, shrink=0),
            # Starship section
            section_header("STARSHIP SYSTEM"),
            flex([
                starship_card("SHIP 35",    "STARSHIP UPPER STAGE",
                              "FLIGHT TEST", YLW, "Starbase, Boca Chica TX",
                              "IFT-9 Preparation"),
                starship_card("BOOSTER 14", "SUPER HEAVY BOOSTER",
                              "STACKING",   BLU, "Starbase, Boca Chica TX",
                              "Integration in progress"),
            ], direction="row", gap="0.75rem",
               grow=0, shrink=0),
        ], direction="column", gap="1rem",
           grow=1, shrink=1, basis="0%",
           pad="1.25rem", overflow="auto"),
    ], direction="column", bg=BG, name="VehiclesRoot")

    write_view("Vehicles", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  PADS
# ═══════════════════════════════════════════════════════════════════════════════
def build_pads():
    pads_data = [
        ("LC-39A",   "LAUNCH COMPLEX 39A · KENNEDY SPACE CENTER, FL",
         "ACTIVE",   "Falcon 9 / Falcon Heavy",  "CRS-33 · Jun 22",  GRN),
        ("SLC-40",   "SPACE LAUNCH COMPLEX 40 · CAPE CANAVERAL, FL",
         "ACTIVE",   "Falcon 9",                 "Starlink 10-5 · Jun 18", GRN),
        ("SLC-4E",   "SPACE LAUNCH COMPLEX 4E · VANDENBERG SFB, CA",
         "ACTIVE",   "Falcon 9",                 "WorldView Legion · Jun 28", GRN),
        ("STARBASE", "BOCA CHICA LAUNCH SITE · BROWNSVILLE, TX",
         "TESTING",  "Starship / Super Heavy",   "IFT-9 · NET Q3 2026", YLW),
    ]

    range_items = [
        ("RANGE SAFETY",    "GO",              GRN),
        ("FLIGHT WEATHER",  "85% FAVORABLE",   GRN),
        ("TRACKING ASSETS", "NOMINAL",         GRN),
        ("RANGE CONTROL",   "MANNED",          BLU),
        ("DOWNRANGE SHIPS", "ON STATION",      GRN),
    ]

    def range_card(title, val, col):
        return flex([
            lbl(title, sz="0.5625rem", col=GRY3, upper=True, track="2px",
                grow=0, shrink=0),
            lbl(val, sz="0.875rem", col=col, bold=True,
                grow=0, shrink=0),
        ], direction="column", gap="0.375rem",
           grow=1, shrink=1, basis="0%",
           bg=CARD, pad="0.875rem 1rem",
           border=f"1px solid {LINE}", radius="1px")

    root = flex([
        embed_view("Components/Nav", grow=0, shrink=0, basis="56px"),
        flex([
            lbl("LAUNCH COMPLEXES", sz="1.375rem", col=WHT,
                bold=True, upper=True, track="4px", grow=0, shrink=0),
            lbl("CCAFS  ·  VAFB  ·  STARBASE",
                sz="0.625rem", col=GRY2, upper=True, track="2px",
                grow=0, shrink=0),
            flex([pad_card(*p) for p in pads_data],
                 direction="row", gap="0.75rem", wrap="wrap",
                 grow=0, shrink=0),
            section_header("EASTERN RANGE STATUS"),
            flex([range_card(*r) for r in range_items],
                 direction="row", gap="0.75rem", wrap="wrap",
                 grow=0, shrink=0),
            section_header("PAD CAMERA FEEDS"),
            flex([
                flex([
                    lbl(label, sz="0.625rem", col=GRY3, upper=True, track="2px",
                        align="center", grow=0, shrink=0),
                    lbl("FEED UNAVAILABLE", sz="0.75rem", col=GRY3,
                        align="center", grow=1, shrink=1),
                ], direction="column", justify="center", align="center",
                   grow=1, shrink=1, basis="0%",
                   bg=CARD, pad="1.5rem 1rem",
                   border=f"1px solid {LINE}", radius="1px",
                   min_height="90px")
                for label in ["LC-39A PAD", "SLC-40 PAD",
                               "SLC-40 TRENCH", "STARBASE OLM"]
            ], direction="row", gap="0.75rem",
               grow=1, shrink=1, basis="0%"),
        ], direction="column", gap="1rem",
           grow=1, shrink=1, basis="0%",
           pad="1.25rem", overflow="auto"),
    ], direction="column", bg=BG, name="PadsRoot")

    write_view("Pads", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  FLEET
# ═══════════════════════════════════════════════════════════════════════════════
def build_fleet():
    def ship_card(name, type_, status, col, loc, mission):
        return flex([
            flex([
                lbl(name,  sz="0.9375rem", col=WHT, bold=True, upper=True,
                    track="1px", grow=1, shrink=1, basis="0%"),
                status_badge(status, col),
            ], direction="row", align="center", gap="0.75rem",
               grow=0, shrink=0),
            lbl(type_, sz="0.5625rem", col=GRY2, upper=True, track="2px",
                grow=0, shrink=0),
            flex([], direction="row", grow=0, shrink=0, basis="1px",
                 backgroundColor=LINE2, alignSelf="stretch"),
            flex([
                flex([lbl("LOCATION", sz="0.5rem", col=GRY3, upper=True, track="2px",
                          grow=0, shrink=0),
                      lbl(loc, sz="0.8125rem", col=GRY1, grow=0, shrink=0)],
                     direction="column", gap="0.25rem", grow=1, shrink=1, basis="0%"),
                flex([lbl("MISSION", sz="0.5rem", col=GRY3, upper=True, track="2px",
                          grow=0, shrink=0),
                      lbl(mission, sz="0.75rem", col=GRY2, grow=0, shrink=0)],
                     direction="column", gap="0.25rem", grow=1, shrink=1, basis="0%"),
            ], direction="row", gap="1rem", grow=0, shrink=0),
        ], direction="column", gap="0.5rem",
           grow=1, shrink=1, basis="0%",
           bg=CARD, pad="1.25rem",
           border=f"1px solid {LINE}", radius="1px")

    asds = [
        ("OCISLY",  "AUTONOMOUS SPACEPORT DRONE SHIP", "DEPLOYED", GRN,
         "Atlantic · 28.5° Inclination",     "Starlink Group 10-5"),
        ("JRTI",    "AUTONOMOUS SPACEPORT DRONE SHIP", "DEPLOYED", GRN,
         "Pacific · SLC-4E Downrange",        "WorldView Legion 3-4"),
        ("NUSQUAM", "AUTONOMOUS SPACEPORT DRONE SHIP", "TRANSIT",  YLW,
         "Gulf of Mexico → Starbase",         "IFT-9 Preparation"),
    ]
    fairing = [
        ("GO MS. CHIEF", "FAIRING RECOVERY VESSEL", "ON STATION", GRN,
         "Atlantic Recovery Zone · 28.5°",    "Starlink 10-5 Fairing"),
        ("GO MS. TREE",  "FAIRING RECOVERY VESSEL", "TRANSIT",    YLW,
         "Port Canaveral → CCAFS",            "Returning from WorldView"),
    ]
    support = [
        ("GO NAVIGATOR", "Support / Tug",         "ACTIVE",  GRN,
         "Port Canaveral, FL",     "Harbor ops"),
        ("GO SEARCHER",  "Crew & Cargo Recovery",  "ACTIVE",  GRN,
         "Atlantic Recovery Zone", "Starlink 10-5"),
        ("GO QUEST",     "Crew Recovery",          "STANDBY", GRY2,
         "Port Canaveral, FL",     "—"),
        ("NRC CYGNUS",   "Offshore Supply",        "TRANSIT", YLW,
         "Gulf of Mexico",         "Starbase resupply"),
    ]

    root = flex([
        embed_view("Components/Nav", grow=0, shrink=0, basis="56px"),
        flex([
            lbl("FLEET STATUS", sz="1.375rem", col=WHT,
                bold=True, upper=True, track="4px", grow=0, shrink=0),
            lbl("RECOVERY VESSELS  ·  SUPPORT SHIPS",
                sz="0.625rem", col=GRY2, upper=True, track="2px",
                grow=0, shrink=0),
            section_header("AUTONOMOUS SPACEPORT DRONE SHIPS"),
            flex([ship_card(*s) for s in asds],
                 direction="row", gap="0.75rem",
                 grow=0, shrink=0),
            section_header("FAIRING RECOVERY VESSELS"),
            flex([ship_card(*s) for s in fairing],
                 direction="row", gap="0.75rem",
                 grow=0, shrink=0),
            section_header("SUPPORT VESSELS"),
            flex([ship_card(*s) for s in support],
                 direction="row", gap="0.75rem", wrap="wrap",
                 grow=0, shrink=0),
        ], direction="column", gap="1rem",
           grow=1, shrink=1, basis="0%",
           pad="1.25rem", overflow="auto"),
    ], direction="column", bg=BG, name="FleetRoot")

    write_view("Fleet", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  EVENTS
# ═══════════════════════════════════════════════════════════════════════════════
def build_events():
    events = [
        ("14:31:07", GRN,  "HIGH",    "STARLINK 10-5", "Vehicle encapsulation complete — fairing closeout nominal"),
        ("14:22:44", BLU,  "INFO",    "RANGE",          "Eastern Range GO for launch on Jun 18 window"),
        ("13:58:12", BLU,  "INFO",    "WEATHER",        "Launch weather: 85% favorable — acceptable winds at 250mb"),
        ("13:40:00", YLW,  "CAUTION", "CRS-33",         "Payload power-on delayed 2h — troubleshooting IMU heater"),
        ("12:30:00", BLU,  "INFO",    "OCISLY",         "OCISLY departed Port Canaveral — on station by T-6h"),
        ("11:14:28", BLU,  "INFO",    "SLC-40",         "Flame deflector water system test complete — NOMINAL"),
        ("10:02:05", BLU,  "INFO",    "B1073",          "Booster B1073.8 propellant loading simulation complete"),
        ("09:30:00", YLW,  "CAUTION", "STARBASE",       "IFT-9 booster 14 stacking paused — GSE inspection"),
        ("08:15:52", BLU,  "INFO",    "CREW-11",        "Crew medical checks complete — crew GO for launch"),
        ("07:44:11", GRN,  "CLEAR",   "WEATHER",        "GOES observation: no upper-level wind anomalies detected"),
        ("06:20:00", BLU,  "INFO",    "FLEET",          "GO Searcher departed Port Canaveral for recovery station"),
        ("05:11:38", RED,  "CRIT",    "CREW-11",        "SCRUB: LC-39A ground support equipment fault — recycling 24h"),
    ]

    def event_row(time_, col, level, source, message):
        return flex([
            lbl(time_,   sz="0.75rem",   col=GRY2, font=FM,
                grow=0, shrink=0, basis="80px"),
            status_badge(level, col),
            lbl(source,  sz="0.6875rem", col=GRY2, upper=True, track="1px",
                grow=0, shrink=0, basis="100px"),
            lbl(message, sz="0.8125rem", col=WHT if col != GRY2 else GRY1,
                grow=1, shrink=1, basis="0%"),
        ], direction="row", align="center", gap="1rem",
           grow=0, shrink=0,
           pad="0.625rem 0.75rem",
           borderBottom=f"1px solid {LINE}")

    root = flex([
        embed_view("Components/Nav", grow=0, shrink=0, basis="56px"),
        flex([
            lbl("EVENTS & ALERTS", sz="1.375rem", col=WHT,
                bold=True, upper=True, track="4px", grow=0, shrink=0),
            lbl("SYSTEM  ·  WEATHER  ·  RANGE  ·  ANOMALIES",
                sz="0.625rem", col=GRY2, upper=True, track="2px",
                grow=0, shrink=0),
            flex([
                table_header(
                    ("TIME UTC",  "80px"), ("LEVEL", "60px"),
                    ("SOURCE",   "100px"), ("EVENT",  "*"),
                ),
                *[event_row(*e) for e in events],
            ], direction="column", gap="0",
               grow=1, shrink=1, basis="0%",
               bg=CARD, border=f"1px solid {LINE}", radius="1px",
               overflow="hidden"),
        ], direction="column", gap="1rem",
           grow=1, shrink=1, basis="0%",
           pad="1.25rem"),
    ], direction="column", bg=BG, name="EventsRoot")

    write_view("Events", root)

# ═══════════════════════════════════════════════════════════════════════════════
#  PROJECT FILES
# ═══════════════════════════════════════════════════════════════════════════════
def write_project():
    write("project.json", {
        "title": "launch", "description": "Launch Operations Control",
        "parent": "", "enabled": True, "inheritable": False
    })
    write("com.inductiveautomation.perspective/page-config/config.json", {
        "pages": {
            "/":          {"title": "Overview",        "viewPath": "Overview"},
            "/launches":  {"title": "Launch Manifest", "viewPath": "Launches"},
            "/vehicles":  {"title": "Vehicle Status",  "viewPath": "Vehicles"},
            "/pads":      {"title": "Launch Pads",     "viewPath": "Pads"},
            "/fleet":     {"title": "Fleet Status",    "viewPath": "Fleet"},
            "/events":    {"title": "Events",          "viewPath": "Events"},
        },
        "sharedDocks": {"cornerPriority": "top-bottom",
                        "bottom": [], "left": [], "right": []}
    })
    write("com.inductiveautomation.perspective/page-config/resource.json",
          resource(["config.json"]))
    print("  project.json + page-config")

# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD + DEPLOY
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Building launch-ops (flex layout, working nav events)...")
    write_project()
    build_nav()
    build_overview()
    build_launches()
    build_vehicles()
    build_pads()
    build_fleet()
    build_events()

    print(f"\nDeploying → {DEST}")
    if os.path.exists(DEST):
        shutil.rmtree(DEST)
    subprocess.run([
        "rsync", "-a",
        "--exclude=.git", "--exclude=tags", "--exclude=*.py",
        f"{SRC}/", f"{DEST}/"
    ], check=True)
    subprocess.run(["find", DEST, "-name", "*.json",
                    "-exec", "touch", "{}", ";"])
    print("Done. Restart gateway to load new views.")
