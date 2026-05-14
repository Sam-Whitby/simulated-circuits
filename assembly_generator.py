#!/usr/bin/env python3
"""
Deterministic assembly instruction generator.

Reads a validated breadboard.yaml (or pointtopoint.yaml in P2P mode) and
writes a human-readable assembly.md.  All hole references, wire counts, and
step content are derived directly from the layout file — no AI text generation.

Exit codes:
  0 — success
  1 — input error

Usage:
    # Breadboard mode (default):
    python3 assembly_generator.py breadboard.yaml assembly.md

    # Point-to-point mode:
    python3 assembly_generator.py --mode p2p pointtopoint.yaml assembly.md

    # Dry-run (print to stdout):
    python3 assembly_generator.py breadboard.yaml
    python3 assembly_generator.py --mode p2p pointtopoint.yaml
"""

import configparser
import os
import sys
import yaml

COLUMNS    = list("ABCDEFGHIJ")
LEFT_HALF  = set("ABCDE")
RIGHT_HALF = set("FGHIJ")


# ── Helpers ───────────────────────────────────────────────────────────────────

def col_index(col: str) -> int:
    return COLUMNS.index(col.upper())


def half_name(col: str) -> str:
    return "left" if col.upper() in LEFT_HALF else "right"


def describe_hole(hole: str) -> str:
    """'J4' → 'J4 (row 4, right half)'"""
    if not hole or hole.startswith("rail") or hole.startswith("ext:") \
            or hole.startswith("pin:"):
        return hole
    col, row = hole[0].upper(), hole[1:]
    return f"{col}{row} (row {row}, {half_name(col)} half)"


def wire_endpoint_text(raw: str, side: str, library: dict | None = None) -> str:
    """Human-readable description of a wire endpoint."""
    s = str(raw).strip()
    if s in ("rail-plus", "rail+"):
        return "the (+) power rail"
    if s in ("rail-minus", "rail-"):
        return "the (−) power rail"
    if s.startswith("ext:"):
        parts = s.split(":")
        if len(parts) == 3:
            comp_id, pin_name = parts[1], parts[2]
            if comp_id == "lcd":
                return f"LCD pin {pin_name} (pin {lcd_pin_number(pin_name)} on the LCD header)"
            return f"{comp_id} module pin {pin_name}"
        return s
    if s.startswith("pin:"):
        ref = s[4:]   # e.g. "esp32.3V3.1"
        pin_label = ref.split(".", 1)[-1]
        # Check if the board type actually supports female-jumper connections
        lib = library or {}
        tap = (lib.get("board-esp32-s3-devkitc-1", {})
               .get("header_info", {}).get("left", {}).get("tap_method", "none"))
        if tap == "female_jumper":
            return (f"the ESP32 header pin '{pin_label}' "
                    f"(plug female jumper onto the pin stub above the PCB)")
        # tap_method != "female_jumper" — this endpoint should have been caught by the validator
        return f"[INVALID: pin:{ref} — left-header tap_method='{tap}'; use P2P mode instead]"
    # Standard hole
    col = s[0].upper()
    row = s[1:]
    return f"hole {col}{row} (row {row}, {half_name(col)} half)"


LCD_PIN_NUMBERS = {
    "VSS": 1, "VDD": 2, "V0": 3, "RS": 4, "RW": 5, "E": 6,
    "D0": 7, "D1": 8, "D2": 9, "D3": 10,
    "D4": 11, "D5": 12, "D6": 13, "D7": 14,
    "A": 15, "K": 16,
}


def lcd_pin_number(pin_name: str) -> str:
    n = LCD_PIN_NUMBERS.get(pin_name.upper())
    return str(n) if n else "?"


def load_library(layout_path: str) -> dict:
    base = os.path.dirname(os.path.abspath(layout_path))
    for path in [os.path.join(base, "parts_library.yaml"),
                 os.path.join(os.path.dirname(base), "parts_library.yaml")]:
        if os.path.exists(path):
            with open(path) as f:
                data = yaml.safe_load(f)
            return data.get("components", {})
    return {}


def load_pio_config(layout_path: str) -> dict:
    """Find and parse the platformio.ini nearest to the layout file."""
    base = os.path.dirname(os.path.abspath(layout_path))
    for directory in [base, os.path.dirname(base)]:
        ini_path = os.path.join(directory, "platformio.ini")
        if os.path.exists(ini_path):
            cfg = configparser.ConfigParser()
            cfg.read(ini_path)
            envs: dict = {}
            for section in cfg.sections():
                if section.startswith("env:"):
                    envs[section[4:]] = dict(cfg[section])
            return {"path": ini_path, "directory": directory, "envs": envs}
    return {}


# ── Breadboard mode ───────────────────────────────────────────────────────────

COMP_DISPLAY_NAMES = {
    "board-esp32-s3-devkitc-1": ("ESP32-S3-DevKitC-1",
                                  "The microcontroller board"),
    "photoresistor-ldr":         ("GL5528 LDR (photoresistor)",
                                  "Any 5 mm LDR works"),
    "resistor":                  ("10 KΩ resistor (brown-black-orange)",
                                  "Pull-down for the voltage divider"),
    "potentiometer-10k":         ("10 KΩ potentiometer (B10K)",
                                  "**2+1 pin type** — two terminals on one side, wiper on the other"),
    "lcd1602-16pin":             ("LCD1602A (16-pin parallel)",
                                  "Connected via wires — does NOT sit on the breadboard"),
    "microsd-spi-module":        ("Micro SD card SPI reader module",
                                  "Connected via 6 jumper wires — does NOT sit on the breadboard"),
}


def parts_list(layout: dict, library: dict) -> str:
    lines = ["## Parts List\n",
             "| Qty | Component | Notes |",
             "|-----|-----------|-------|"]

    for comp in layout.get("components", []) + layout.get("external_components", []):
        ctype = comp.get("type", "")
        name, note = COMP_DISPLAY_NAMES.get(ctype, (ctype, ""))
        lines.append(f"| 1 | {name} | {note} |")

    wires = layout.get("wires", [])
    # Only count female-to-male wires when the library confirms female jumpers are feasible
    left_tap = (library.get("board-esp32-s3-devkitc-1", {})
                .get("header_info", {}).get("left", {}).get("tap_method", "none"))
    pin_wires = [w for w in wires if str(w.get("from","")).startswith("pin:")]
    female_count = len(pin_wires) if left_tap == "female_jumper" else 0
    male_count   = len(wires) - len(pin_wires)
    if female_count:
        wire_desc = f"{male_count} male-to-male + {female_count} female-to-male"
    else:
        wire_desc = str(len(wires))
    lines.append(f"| 1 | Full-size breadboard (830 points, 63 rows) | |")
    lines.append(f"| — | Jumper wires ({wire_desc}) | Assorted colours |")
    lines.append("| 1 | USB-C cable | To power the ESP32 and upload firmware |")
    return "\n".join(lines)


BREADBOARD_PRIMER = """\
## Breadboard Primer

A full-size breadboard has:
- **Rows 1–63**, numbered from top to bottom.
- **Columns A–J**, labelled across each row.
- A **centre gap** that splits each row into two independent halves:
  - Left half: columns A–E (all five holes in the same row are connected).
  - Right half: columns F–J (same rule — connected within the half).
- **Power rails** running the full length on each side: `(+)` and `(−)`.

**The one-hole-one-pin rule**: each hole holds exactly one lead or one wire pin.
If a component occupies A4, a wire to the same node must use a different free
hole in the same row-half.

**The ESP32 body rule**: the ESP32-S3-DevKitC-1 PCB physically covers
**rows 1–26, columns A–I**.  Only the actual header pin holes (A1–A22 and
I1–I22) are accessible in this zone.  Left-header pins (col A, rows 1–22)
have no adjacent free hole — columns B–E in those rows are blocked by the
PCB body.  For right-header GPIO pins, use column J (same right-half row —
J is outside the PCB body and always accessible).

**Left-header connections**: the `parts_library.yaml` `header_info.left.tap_method`
field determines whether left-header pins can be tapped.  If `"none"` (the
default for this board variant), circuits that require left-header connections
must use point-to-point (P2P) assembly instead of a breadboard."""


def pot_id_guide(layout: dict) -> str:
    pot = next((c for c in layout.get("components", [])
                if c.get("type") == "potentiometer-10k"), None)
    if not pot:
        return ""
    pins = pot.get("pins", {})
    rows = []
    if "gnd-end" in pins:
        rows.append(f"| GND terminal (top) | {pins['gnd-end']} | → power rail (−) |")
    if "vcc-end" in pins:
        rows.append(f"| VCC terminal (bottom) | {pins['vcc-end']} | → power rail (+) |")
    if "wiper" in pins:
        rows.append(f"| Wiper | {pins['wiper']} | → LCD contrast wire |")

    table = "\n".join(rows)
    return f"""\
## Potentiometer Pin Identification

The potentiometer has **three pins in a 2+1 arrangement**: two terminal pins
on one face, one wiper pin on the opposite face.

1. Hold the pot with the shaft pointing up and the pins facing down.
2. On **one face** you will see **two pins** side by side — these are the terminals.
3. On the **opposite face** you will see **one pin** in the centre — the wiper.

Rotate the pot **90°** so the two terminals sit in the **same column but
different rows** (2 rows apart), with the wiper 2 columns to the right.

| Pin | Hole | Function |
|-----|------|---------|
{table}"""


def esp32_pin_table(layout: dict) -> str:
    esp32 = next((c for c in layout.get("components", [])
                  if c.get("type") == "board-esp32-s3-devkitc-1"), None)
    if not esp32:
        return ""

    pins = esp32.get("pins", {})

    left_pins  = [(pn, h) for pn, h in pins.items() if str(h).startswith("A")]
    right_pins = [(pn, h) for pn, h in pins.items() if str(h).startswith("I")]
    left_pins.sort(key=lambda x: int(str(x[1])[1:]))
    right_pins.sort(key=lambda x: int(str(x[1])[1:]))

    header = (
        "## ESP32-S3 Pin Reference\n\n"
        "GPIO numbers do **not** equal row numbers (e.g. GPIO8 is at row 12).\n"
        "The board body covers **rows 1–26, cols A–I** — only the header pin holes\n"
        "and col J (outside body) are accessible in that zone.\n\n"
        "| Row | Left (col A) | Used? | Row | Right (col I) | Used? |\n"
        "|-----|-------------|-------|-----|--------------|-------|"
    )
    rows = [header]
    for i in range(max(len(left_pins), len(right_pins))):
        lpn, lh = left_pins[i] if i < len(left_pins) else ("", "")
        rpn, rh = right_pins[i] if i < len(right_pins) else ("", "")
        lrow = str(lh)[1:] if lh else ""
        rrow = str(rh)[1:] if rh else ""

        lused = next((w.get("purpose","") for w in layout.get("wires", [])
                      if str(w.get("from","")).startswith("pin:esp32")
                      and lpn in str(w.get("from",""))), "")
        if not lused:
            j_hole = f"J{lrow}"
            lused = next((w.get("purpose","") for w in layout.get("wires", [])
                          if str(w.get("from","")) == j_hole or
                          str(w.get("to","")) == j_hole), "")
        j_hole_r = f"J{rrow}"
        rused = next((w.get("purpose","") for w in layout.get("wires", [])
                      if str(w.get("from","")) == j_hole_r or
                      str(w.get("to","")) == j_hole_r), "")

        lpn_disp = f"**{lpn}**" if lused else lpn
        rpn_disp = f"**{rpn}**" if rused else rpn

        rows.append(f"| {lrow} | {lpn_disp} | {lused[:40] or '—'} "
                    f"| {rrow} | {rpn_disp} | {rused[:40] or '—'} |")
    return "\n".join(rows)


def assembly_steps(layout: dict, library: dict) -> str:
    wires = layout.get("wires", [])
    components     = layout.get("components", [])
    ext_components = layout.get("external_components", [])

    has_ldr  = any(c.get("type") == "photoresistor-ldr"  for c in components)
    has_pot  = any(c.get("type") == "potentiometer-10k"  for c in components)
    has_lcd  = any(c.get("type") == "lcd1602-16pin"      for c in ext_components)
    has_ext  = bool(ext_components)

    esp32_lib = library.get("board-esp32-s3-devkitc-1", {})
    left_tap  = esp32_lib.get("header_info", {}).get("left", {}).get("tap_method", "none")
    orientation_cue = esp32_lib.get("orientation_cue",
                                    "USB-C port facing away from row 1 (the top of the breadboard)")

    out = []
    part = ord("A")

    # ── Part A — place ESP32 ─────────────────────────────────────────────────
    out.append(f"""\
### Part {'A'} — Place the ESP32-S3 board

**A1.** Orient the breadboard with row 1 at the top.

**A2.** Hold the ESP32-S3-DevKitC-1 with: {orientation_cue}.

**A3.** Press the board firmly into the breadboard so that:
- The left header pins go into **column A, rows 1–22**.
- The right header pins go into **column I, rows 1–22**.
- The board straddles the centre gap.

The board PCB covers rows 1–26, cols A–I.  Do not place anything in that zone.
Column J (rows 1–22) is outside the board body and accessible for wiring.""")
    part += 1

    # ── Part B — power rails ─────────────────────────────────────────────────
    pl = chr(part)
    out.append(f"\n### Part {pl} — Set up the power rails\n")
    step_n = 1
    for w in wires:
        purpose = str(w.get("purpose", "")).upper()
        fr = str(w.get("from", ""))
        to = str(w.get("to", ""))
        is_power = (
            not fr.startswith("ext:") and not to.startswith("ext:") and (
                "VCC" in purpose or "3V3" in purpose or "GND" in purpose or
                ("rail" in to.lower() and fr.startswith("pin:")) or
                ("rail" in fr.lower() and to.startswith("pin:"))
            )
        )
        # Exclude SPI/signal wires that happen to mention ext components
        is_signal = any(x in purpose for x in
                        ["MOSI","MISO","SCK","CS","RS","RS","EN","D4","D5","D6","D7",
                         "ADC","LDR","RES","LCD","POT","WIPER","CONTRAST"])
        if not is_power or is_signal:
            continue
        colour = str(w.get("color", "red" if "3V3" in purpose or "VCC" in purpose else "black"))
        if fr.startswith("pin:") and left_tap == "female_jumper":
            out.append(
                f"**{pl}{step_n}.** Take a **{colour} female-to-male** jumper wire.  "
                f"Plug the **female (socket) end** onto the ESP32 header pin "
                f"`{fr[4:].split('.',1)[-1]}` (the pin stub protrudes above the PCB).  "
                f"Insert the **male end** into {wire_endpoint_text(to, 'to', library)}."
            )
        elif fr.startswith("pin:"):
            # pin: wire present but tap_method != female_jumper — should have been
            # caught by the validator; output a clear error marker rather than bad instructions
            out.append(
                f"**{pl}{step_n}.** [ERROR: wire '{w.get('purpose',fr)}' uses a pin: "
                f"endpoint but left-header tap_method='{left_tap}'. "
                f"This layout must be redesigned or switched to P2P mode.]"
            )
        else:
            out.append(
                f"**{pl}{step_n}.** Take a **{colour}** jumper wire.  "
                f"Insert one end into {wire_endpoint_text(fr, 'from', library)}.  "
                f"Connect the other end to {wire_endpoint_text(to, 'to', library)}."
            )
        step_n += 1
    part += 1

    # ── Part C — LDR (conditional) ───────────────────────────────────────────
    if has_ldr:
        pl = chr(part)
        out.append(f"\n### Part {pl} — Light sensor (LDR voltage divider)\n")
        ldr = next((c for c in components if c.get("type") == "photoresistor-ldr"), None)
        res = next((c for c in components if c.get("type") == "resistor"), None)
        ldr_lib = library.get("photoresistor-ldr", {})
        ldr_bend = ldr_lib.get("lead_bend_note",
                               "bend leads for vertical insertion in adjacent rows")
        if ldr and res:
            l1 = ldr["pins"].get("lead-1", "?")
            l2 = ldr["pins"].get("lead-2", "?")
            r1 = res["pins"].get("lead-1", "?")
            r2 = res["pins"].get("lead-2", "?")
            out.append(
                f"The LDR and 10 KΩ resistor form a voltage divider.  "
                f"The ESP32 reads the midpoint.\n\n"
                f"**{pl}1.** {ldr_bend.capitalize()}.  "
                f"Insert into **{l1}** and **{l2}** (either lead, LDR has no polarity).\n\n"
                f"**{pl}2.** Bend the 10 KΩ resistor leads for vertical insertion.  "
                f"Insert **lead-1 into {r1}**, **lead-2 into {r2}**.\n"
                f"  ({r1} is in the same right-half row as {l2} — they are connected.)\n"
            )
        step_n = 3
        for w in wires:
            purpose = str(w.get("purpose", "")).lower()
            if any(x in purpose for x in ["ldr", "resistor", "junction", "adc"]):
                fr = str(w.get("from", ""))
                to = str(w.get("to", ""))
                colour = str(w.get("color", "gray"))
                out.append(
                    f"**{pl}{step_n}.** Take a **{colour}** jumper wire.  "
                    f"Insert one end into {wire_endpoint_text(fr, 'from', library)}.  "
                    f"Connect the other end to {wire_endpoint_text(to, 'to', library)}.\n"
                    f"  _{w.get('purpose', '')}_"
                )
                step_n += 1
        part += 1

    # ── Part D — potentiometer (conditional) ─────────────────────────────────
    if has_pot:
        pl = chr(part)
        out.append(f"\n### Part {pl} — Potentiometer (LCD contrast)\n")
        pot = next((c for c in components if c.get("type") == "potentiometer-10k"), None)
        if pot:
            pins = pot.get("pins", {})
            gnd = pins.get("gnd-end", "?")
            vcc = pins.get("vcc-end", "?")
            wip = pins.get("wiper", "?")
            out.append(
                "Read the Potentiometer Pin Identification section above before continuing.\n\n"
                f"**{pl}1.** Orient the pot with the two terminals facing column C and the "
                f"wiper facing column E.\n\n"
                f"**{pl}2.** Insert the **GND terminal** into **{gnd}**.\n\n"
                f"**{pl}3.** Insert the **VCC terminal** into **{vcc}**.\n\n"
                f"**{pl}4.** Insert the **wiper** into **{wip}**.\n"
            )
        step_n = 5
        for w in wires:
            purpose = str(w.get("purpose", "")).lower()
            if any(x in purpose for x in ["pot", "potentiometer", "wiper", "contrast"]):
                fr = str(w.get("from", ""))
                to = str(w.get("to", ""))
                colour = str(w.get("color", "gray"))
                out.append(
                    f"**{pl}{step_n}.** Take a **{colour}** jumper wire.  "
                    f"Insert one end into {wire_endpoint_text(fr, 'from', library)}.  "
                    f"Connect the other end to {wire_endpoint_text(to, 'to', library)}.\n"
                    f"  _{w.get('purpose', '')}_"
                )
                step_n += 1
        part += 1

    # ── Part E — external components ──────────────────────────────────────────
    if has_ext:
        pl = chr(part)
        if has_lcd:
            out.append(f"""\

### Part {pl} — LCD1602A (connected externally via jumper wires)

The LCD1602A PCB (80×36 mm) is too large to sit on the breadboard.
Place it **beside** the breadboard and wire each of its 16 pins as below.
Solder a 16-pin male header to the LCD if not already fitted.

| LCD pin | Label | Connect to | Wire colour |
|---------|-------|------------|-------------|""")

            lcd_wires: dict = {}
            for w in wires:
                to_s = str(w.get("to", ""))
                fr_s = str(w.get("from", ""))
                if to_s.startswith("ext:lcd:"):
                    pin = to_s.split(":")[-1]
                    lcd_wires[pin] = (wire_endpoint_text(fr_s, "from", library), w.get("color", "—"))
                elif fr_s.startswith("ext:lcd:"):
                    pin = fr_s.split(":")[-1]
                    lcd_wires[pin] = (wire_endpoint_text(to_s, "to", library), w.get("color", "—"))

            lcd_order = ["VSS","VDD","V0","RS","RW","E","D0","D1","D2","D3",
                         "D4","D5","D6","D7","A","K"]
            for pin in lcd_order:
                num = LCD_PIN_NUMBERS.get(pin, "?")
                if pin in lcd_wires:
                    conn, colour = lcd_wires[pin]
                    out.append(f"| {num} | {pin} | {conn} | {colour} |")
                elif pin in ("D0","D1","D2","D3"):
                    out.append(f"| {num} | {pin} | *(leave unconnected — 4-bit mode)* | — |")
                else:
                    out.append(f"| {num} | {pin} | *(not connected)* | — |")
        else:
            # Generic external-component wiring section
            out.append(f"\n### Part {pl} — External component connections\n")
            for ec in ext_components:
                eid = ec.get("id", "")
                ename, _ = COMP_DISPLAY_NAMES.get(ec.get("type",""), (ec.get("type",""), ""))
                conns = ec.get("connections", {})
                out.append(f"**{ename}** (`{eid}`) — connect via jumper wires:\n")
                out.append("| Module pin | Connect to | Wire colour | Purpose |")
                out.append("|------------|------------|-------------|---------|")
                # All connections derived from the wires list (single source of truth)
                for w in wires:
                    fr_s = str(w.get("from",""))
                    to_s = str(w.get("to",""))
                    prefix = f"ext:{eid}:"
                    if fr_s.startswith(prefix):
                        pin = fr_s[len(prefix):]
                        out.append(f"| {pin} | {wire_endpoint_text(to_s,'to',library)} "
                                   f"| {w.get('color','—')} | {w.get('purpose','—')} |")
                    elif to_s.startswith(prefix):
                        pin = to_s[len(prefix):]
                        out.append(f"| {pin} | {wire_endpoint_text(fr_s,'from',library)} "
                                   f"| {w.get('color','—')} | {w.get('purpose','—')} |")
                out.append("")
        part += 1

    # ── Final part — verification ─────────────────────────────────────────────
    pl = chr(part)
    out.append(f"\n\n### Part {pl} — Verification checklist and power-on test\n")
    out.append("Verify all wires before applying power:\n")
    out.append("| # | From | To | Colour | Purpose |")
    out.append("|---|------|----|--------|---------|")
    for i, w in enumerate(wires, 1):
        fr = str(w.get("from", ""))
        to = str(w.get("to", ""))
        fr = fr.replace("rail-plus","(+) rail").replace("rail-minus","(−) rail")
        to = to.replace("rail-plus","(+) rail").replace("rail-minus","(−) rail")
        if fr.startswith("ext:"):
            parts = fr.split(":")
            fr = f"{parts[1]} pin {parts[2]}" if len(parts) == 3 else fr
        if to.startswith("ext:"):
            parts = to.split(":")
            to = f"{parts[1]} pin {parts[2]}" if len(parts) == 3 else to
        if fr.startswith("pin:"):
            pin_label = fr[4:].split(".", 1)[-1]
            suffix = " (female jumper)" if left_tap == "female_jumper" else " [INVALID pin: endpoint]"
            fr = f"ESP32 pin {pin_label}{suffix}"
        out.append(f"| {i} | {fr} | {to} | {w.get('color','—')} | {w.get('purpose','—')} |")

    # Circuit-specific power-on hints
    circuit = layout.get("circuit", "").lower()
    checklist = [
        "Confirm all wires are connected as above.",
        "Connect the USB-C cable to the ESP32.",
    ]
    if has_pot:
        checklist.insert(1, "Turn the potentiometer knob to the mid-position.")
    if has_lcd:
        checklist += [
            "The LCD backlight should illuminate within 1–2 seconds.",
            "Adjust the potentiometer if the LCD text is faint or invisible.",
        ]
    if "ldr" in circuit or "light" in circuit or has_ldr:
        checklist += [
            "Cover the LDR — the sensor reading should decrease.",
            "Uncover and hold a torch close — the reading should increase.",
        ]
    if "midi" in circuit or "sdcard" in "".join(ec.get("type","") for ec in ext_components):
        checklist += [
            "Open a serial monitor at 115200 baud.",
            'Confirm you see {"status":"SD_OK"} or {"status":"SD_FAIL"}.',
            "Connect the keyboard via USB cable → Mepsies OTG adapter → ESP32 USB port.",
            'Play a note — a JSON line with "note": should appear in the serial log.',
        ]

    out.append("\n**Power-on checklist:**\n")
    for n, item in enumerate(checklist, 1):
        out.append(f"{n}. {item}")

    return "\n\n".join(out)


def generate_power_section(layout: dict, library: dict) -> str:
    """Explain power source and flag unconnected rails."""
    wires  = layout.get("wires", [])
    circuit = layout.get("circuit", "").lower()

    rail_plus_used = any(
        str(w.get("from","")) in ("rail-plus","rail+") or
        str(w.get("to",""))   in ("rail-plus","rail+")
        for w in wires
    )
    rail_plus_sourced = any(
        str(w.get("to","")) in ("rail-plus","rail+") and
        str(w.get("from","")).startswith("pin:")
        for w in wires
    )

    lines: list[str] = ["## Power\n"]

    if rail_plus_used and not rail_plus_sourced:
        lines += [
            "> **Warning — (+) power rail has no source.**",
            ">",
            "> This layout uses the (+) breadboard power rail but contains no wire that",
            "> feeds 3.3 V into the rail.  The ESP32-S3's 3V3 pins (A1, A2) are on the",
            "> left header where `tap_method = 'none'` — they cannot be tapped from the",
            "> breadboard.  You must connect an external 3.3 V supply to the (+) rail",
            "> before powering on, or rebuild this circuit in point-to-point (P2P) mode.",
            "",
        ]

    lines += [
        "**ESP32 power source**: Connect a USB-C cable to the **COM port** (the USB-C",
        "port on the ESP32-S3-DevKitC-1 connected to the on-board USB bridge chip).",
        "Plug the other end into a computer or USB charger (≥ 500 mA).",
    ]

    if "midi" in circuit or "usb host" in circuit:
        lines += [
            "",
            "**The ESP32-S3-DevKitC-1 has two USB-C ports:**",
            "",
            "| Port | Label | Purpose |",
            "|------|-------|---------|",
            "| COM  | `COM` | Power in, serial monitor, firmware upload |",
            "| OTG  | `USB` | USB host — receives MIDI data from keyboard |",
            "",
            "> The keyboard USB cable carries **MIDI data only**.  It does **not** power",
            "> the ESP32.  Always connect the COM port to power before use.",
        ]

    return "\n".join(lines)


def generate_firmware_section(layout: dict, layout_path: str) -> str:
    """Generate firmware upload/monitor instructions derived from platformio.ini."""
    pio = load_pio_config(layout_path)
    if not pio or not pio.get("envs"):
        return ""

    circuit = layout.get("circuit", "").lower()
    pio_dir = pio["directory"]
    env           = next(iter(pio["envs"].values()))
    monitor_speed = env.get("monitor_speed", "115200")
    build_flags   = env.get("build_flags", "")
    has_wokwi     = "WOKWI_SIMULATION" in build_flags.upper()

    # Find configure_firmware.py; compute relative path from pio_dir
    cfg_rel: str | None = None
    for d in [pio_dir, os.path.dirname(pio_dir)]:
        p = os.path.join(d, "configure_firmware.py")
        if os.path.exists(p):
            cfg_rel = os.path.relpath(p, pio_dir)
            break

    lines: list[str] = [
        "## Firmware\n",
        f"All commands run from the project directory:\n",
        f"```\ncd {pio_dir}\n```\n",
    ]

    if cfg_rel:
        cfg = f"python3 {cfg_rel}"
        if has_wokwi:
            lines += [
                "> The firmware is currently configured for **Wokwi simulation**",
                "> (`-DWOKWI_SIMULATION=1`).  The commands below switch modes automatically.",
                "",
            ]
        lines += [
            "### Flash to real hardware\n",
            "```",
            f"{cfg} hw && pio run --target upload && {cfg} sim",
            "```\n",
            "Switches to hardware mode → uploads → restores simulation mode.\n",
        ]
        if has_wokwi and "midi" in circuit:
            lines += [
                "> Note: the full USB MIDI host driver is currently stubbed.",
                "> See `src/main.cpp` for implementation notes.",
                "",
            ]
        lines += [
            "### Switch mode manually\n",
            "```",
            f"{cfg} hw      # real hardware (USB OTG enabled)",
            f"{cfg} sim     # Wokwi simulation",
            f"{cfg} status  # show current mode",
            "```\n",
        ]
    else:
        # Fallback: no configure_firmware.py found
        if has_wokwi:
            lines += [
                "> **`WOKWI_SIMULATION=1` is active** — edit `platformio.ini` to remove",
                "> this flag and add `-DARDUINO_USB_MODE=0` before flashing real hardware.",
                "",
            ]
        lines += [
            "### Upload\n",
            "```\npio run --target upload\n```\n",
        ]

    lines += [
        "### Monitor\n",
        f"```\npio device monitor --baud {monitor_speed}\n```\n",
    ]

    if "midi" in circuit:
        lines += [
            "Expected serial output after successful SD initialisation:\n",
            "```json",
            '{"status":"SD_OK"}',
            '{"t":12345,"note":60,"vel":64,"type":"noteOn","ch":1}',
            "```\n",
            'If the SD card is absent or fails you will see `{"status":"SD_FAIL"}` instead.\n',
        ]
    elif "ldr" in circuit or "light" in circuit:
        lines += [
            "Expected serial output:\n",
            "```",
            "ADC: 2048  Lux: 245",
            "```\n",
        ]

    return "\n".join(lines)


def generate_breadboard_md(layout: dict, layout_path: str = "") -> str:
    library = load_library(layout_path) if layout_path else {}
    circuit = layout.get("circuit", "Circuit")
    has_pot = any(c.get("type") == "potentiometer-10k"
                  for c in layout.get("components", []))
    sections = [
        f"# Assembly Instructions — {circuit}\n",
        "> **Generated deterministically from a validated `breadboard.yaml` layout.**\n"
        "> Every hole reference was verified by `breadboard_validator.py`.\n",
        "---\n",
        parts_list(layout, library),
        "---\n",
        BREADBOARD_PRIMER,
        "---\n",
    ]
    if has_pot:
        sections += [pot_id_guide(layout), "---\n"]
    firmware_md = generate_firmware_section(layout, layout_path)
    sections += [
        esp32_pin_table(layout),
        "---\n",
        generate_power_section(layout, library),
        "---\n",
        "## Step-by-Step Assembly\n\nWork in order. Complete each step before moving on.\n",
        "---\n",
        assembly_steps(layout, library),
    ]
    if firmware_md:
        sections += ["---\n", firmware_md]
    return "\n\n".join(s for s in sections if s)


# ── P2P mode ──────────────────────────────────────────────────────────────────

def generate_p2p_md(layout: dict, layout_path: str = "") -> str:
    wires = layout.get("wires", [])
    circuit = layout.get("circuit", "Circuit")
    library = load_library(layout_path) if layout_path else {}
    firmware_md = generate_firmware_section(layout, layout_path) if layout_path else ""
    out = [
        f"# Assembly Instructions — {circuit} (Point-to-Point)\n",
        "> **Generated deterministically from `pointtopoint.yaml`.**\n"
        "> No breadboard required.\n",
        "---\n",
        "## Overview\n\n"
        "Point-to-point (P2P) wiring connects component leads directly with jumper "
        "wires — no breadboard is used.  Lay the ESP32 flat on a non-conductive "
        "surface (foam, cardboard, or a silicone mat).  Keep wires short and "
        "label or colour-code them to match this guide.\n\n"
        "For junction nodes (nets with 3 or more endpoints), the first endpoint "
        "listed is the hub: additional wires daisy-chain from that hub wire.\n\n"
        "In P2P mode the ESP32 is NOT inserted into a breadboard, so left-header pins "
        "are accessible: plug female-to-male jumper wires directly onto the pin stubs "
        "that protrude below the underside of the PCB.\n",
        "---\n",
        generate_power_section(layout, library),
        "---\n",
        "## Wire-by-Wire Assembly\n",
        f"Total wires to connect: **{len(wires)}**\n",
    ]

    current_net = None
    step = 1
    for w in wires:
        net = w.get("net", "")
        if net != current_net:
            out.append(f"\n### Net: {net}\n")
            current_net = net

        fr   = w.get("from", "")
        to   = w.get("to", "")
        col  = w.get("color", "gray")
        fnot = w.get("from_note", fr)
        tnot = w.get("to_note", to)
        purp = w.get("purpose", net)

        out.append(
            f"**Step {step}.** Take a **{col}** jumper wire.\n"
            f"- Connect one end to: **{fr}** — {fnot}\n"
            f"- Connect the other end to: **{to}** — {tnot}\n"
            f"- _Purpose: {purp}_\n"
        )
        step += 1

    out.append("\n---\n")
    out.append("## Verification\n\n"
               "1. Trace every wire against the list above before powering on.\n"
               "2. Confirm no two wires share the same two endpoints (no duplicates).\n"
               "3. Verify all junction nodes have their hub wire connected before "
               "adding spoke wires.\n"
               "4. Connect USB-C and verify the system starts up correctly.")

    if firmware_md:
        out.append("\n---\n")
        out.append(firmware_md)

    return "\n".join(out)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    mode = "breadboard"

    if "--mode" in args:
        idx = args.index("--mode")
        mode = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if not args:
        print("Usage: assembly_generator.py [--mode breadboard|p2p] <layout.yaml> [output.md]",
              file=sys.stderr)
        sys.exit(1)

    layout_path = args[0]
    output_path = args[1] if len(args) > 1 else None

    with open(layout_path) as f:
        layout = yaml.safe_load(f)

    if mode == "p2p":
        md = generate_p2p_md(layout, layout_path)
    else:
        md = generate_breadboard_md(layout, layout_path)

    if output_path:
        with open(output_path, "w") as f:
            f.write(md)
        wire_count = len(layout.get("wires", []))
        print(f"OK — assembly.md written to '{output_path}' "
              f"({wire_count} wires documented)")
    else:
        print(md)

    sys.exit(0)


if __name__ == "__main__":
    main()
