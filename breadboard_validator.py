#!/usr/bin/env python3
"""
Breadboard physical constraint validator.

Checks a breadboard.yaml layout for five classes of error:
  1. HOLE CONFLICT       — two component pins assigned to the same hole
  2. WIRE IN OCCUPIED HOLE — a jumper wire endpoint is in a pin-occupied hole
  3. BODY OVERLAP        — a component's bounding box physically overlaps another's
  4. BREADBOARD TOO SMALL — layout exceeds the declared row count
  5. PIN LAYOUT MISMATCH — declared pin holes don't match parts_library.yaml spacing
     (loaded from parts_library.yaml if present alongside breadboard.yaml)

  BONUS: if parts_library.yaml marks a component type as external_only: true,
  placing it directly on the board is reported as an error.

Usage:
    python3 breadboard_validator.py breadboard.yaml [parts_library.yaml]
    python3 breadboard_validator.py breadboard.yaml   # auto-finds parts_library.yaml

Exit 0 = valid.  Exit 1 = one or more violations found.
"""

import os
import sys
import yaml

COLUMNS = list("ABCDEFGHIJ")
LEFT_HALF  = set("ABCDE")
RIGHT_HALF = set("FGHIJ")
DEFAULT_MAX_ROWS = 63
RAIL_PREFIXES     = ("rail-", "rail+", "rail_")
EXTERNAL_PREFIXES = ("external:", "ext:", "pin:")  # "pin:" = female wire onto MCU header pin


# ── Helpers ──────────────────────────────────────────────────────────────────

def col_index(col: str) -> int:
    return COLUMNS.index(col.upper())


def parse_hole(hole: str):
    """Parse 'A1', 'J22', etc.
    Returns (col_str, row_int) or None for rails, external refs, or invalid."""
    if not hole:
        return None
    s = str(hole).strip()
    sl = s.lower()
    if any(sl.startswith(p) for p in RAIL_PREFIXES):
        return None
    if any(sl.startswith(p) for p in EXTERNAL_PREFIXES):
        return None
    col = s[0].upper()
    if col not in COLUMNS:
        return None
    try:
        return col, int(s[1:])
    except ValueError:
        return None


def same_half(col1: str, col2: str) -> bool:
    return (col1.upper() in LEFT_HALF) == (col2.upper() in LEFT_HALF)


# ── Parts library ─────────────────────────────────────────────────────────────

def load_library(breadboard_path: str, explicit_path: str | None = None) -> dict:
    """
    Load parts_library.yaml.  Searches:
      1. Explicit path passed on CLI.
      2. Same directory as breadboard.yaml.
    Returns {} if no library found (validator proceeds without library checks).
    """
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    # Auto-discover alongside the breadboard file, then in the parent directory
    base = os.path.dirname(os.path.abspath(breadboard_path))
    candidates.append(os.path.join(base, "parts_library.yaml"))
    candidates.append(os.path.join(os.path.dirname(base), "parts_library.yaml"))

    for path in candidates:
        if os.path.exists(path):
            with open(path) as f:
                lib = yaml.safe_load(f)
            if lib and isinstance(lib.get("components"), dict):
                print(f"INFO: parts library loaded from '{path}'")
                return lib["components"]
    print("INFO: no parts_library.yaml found — skipping library checks")
    return {}


def validate_pin_layout(comp_id: str, comp_type: str,
                        declared_pins: dict, lib_spec: dict,
                        errors: list) -> str | None:
    """
    Verify that declared pin positions match the library pin-layout offsets.
    Returns the anchor hole string (e.g. 'C33') if validation succeeds,
    or None on failure.
    """
    lib_pins = lib_spec.get("pins", {})
    if not lib_pins:
        return None

    anchor_name = next(iter(lib_pins))
    if anchor_name not in declared_pins:
        errors.append(
            f"PIN LAYOUT: {comp_id} (type={comp_type}) is missing anchor pin "
            f"'{anchor_name}' required by parts_library"
        )
        return None

    anchor = parse_hole(str(declared_pins[anchor_name]))
    if anchor is None:
        errors.append(
            f"PIN LAYOUT: {comp_id}.{anchor_name} is not a valid hole reference"
        )
        return None
    anchor_col, anchor_row = anchor
    anchor_col_idx = col_index(anchor_col)

    for pin_name, offsets in lib_pins.items():
        if pin_name == anchor_name or pin_name not in declared_pins:
            continue
        dc = offsets.get("offset_col", 0)
        dr = offsets.get("offset_row", 0)
        exp_col_idx = anchor_col_idx + dc
        exp_row = anchor_row + dr

        parsed = parse_hole(str(declared_pins[pin_name]))
        if parsed is None:
            continue
        act_col_idx = col_index(parsed[0])
        act_row = parsed[1]

        if act_col_idx != exp_col_idx or act_row != exp_row:
            exp_col = (COLUMNS[exp_col_idx]
                       if 0 <= exp_col_idx < len(COLUMNS) else "?")
            errors.append(
                f"PIN LAYOUT MISMATCH: {comp_id}.{pin_name} is at "
                f"{parsed[0]}{act_row}, but parts_library expects "
                f"{exp_col}{exp_row} "
                f"({dc:+d} cols, {dr:+d} rows from anchor "
                f"'{anchor_name}' at {anchor_col}{anchor_row})"
            )

    return f"{anchor_col}{anchor_row}"


def library_body_box(comp_id: str,
                     declared_pins: dict, lib_spec: dict) -> tuple | None:
    """
    Compute the body bounding box from parts_library body_breadboard offsets
    and the anchor pin position.
    Returns (top_row, bottom_row, left_col, right_col, comp_id) or None.
    """
    body = lib_spec.get("body_breadboard")
    lib_pins = lib_spec.get("pins", {})
    if not body or not lib_pins:
        return None

    anchor_name = next(iter(lib_pins))
    if anchor_name not in declared_pins:
        return None

    anchor = parse_hole(str(declared_pins[anchor_name]))
    if anchor is None:
        return None
    anchor_col, anchor_row = anchor
    anchor_col_idx = col_index(anchor_col)

    top    = anchor_row  - body.get("rows_above_anchor", 0)
    bottom = anchor_row  + body.get("rows_below_anchor", 0)
    lci    = anchor_col_idx - body.get("cols_left_of_anchor", 0)
    rci    = anchor_col_idx + body.get("cols_right_of_anchor", 0)

    lc = COLUMNS[max(0, lci)]
    rc = COLUMNS[min(len(COLUMNS) - 1, rci)]
    return top, bottom, lc, rc, comp_id


# ── Main validator ────────────────────────────────────────────────────────────

def validate(breadboard_path: str, library_path: str | None = None) -> list[str]:
    with open(breadboard_path) as f:
        layout = yaml.safe_load(f)

    library = load_library(breadboard_path, library_path)

    errors: list[str] = []
    occupied: dict[str, str] = {}   # "A1" → "esp32.3V3.1"
    bodies:   list[tuple] = []      # (top, bottom, lc, rc, id)

    # ── 1. Register component pins, validate layouts, collect body boxes ───────
    for comp in layout.get("components", []):
        cid      = comp.get("id", "<unnamed>")
        ctype    = comp.get("type", "")
        lib_spec = library.get(ctype, {}) if ctype else {}

        # Check external_only flag
        if lib_spec.get("external_only"):
            errors.append(
                f"EXTERNAL ONLY: '{cid}' has type '{ctype}' which parts_library "
                f"marks as external_only — it must NOT be placed directly on the "
                f"breadboard (it is too large; connect via jumper wires instead)"
            )

        # Pin occupancy
        for pin_name, raw_hole in comp.get("pins", {}).items():
            parsed = parse_hole(str(raw_hole))
            if parsed is None:
                errors.append(f"INVALID HOLE: {cid}.{pin_name} = '{raw_hole}'")
                continue
            col, row = parsed
            key = f"{col}{row}"
            if key in occupied:
                errors.append(
                    f"HOLE CONFLICT: {key} is claimed by both "
                    f"'{occupied[key]}' and '{cid}.{pin_name}'"
                )
            else:
                occupied[key] = f"{cid}.{pin_name}"

        # Pin layout validation against library
        if lib_spec and lib_spec.get("pins"):
            validate_pin_layout(cid, ctype, comp.get("pins", {}),
                                lib_spec, errors)

        # Determine body bounding box:
        # Prefer library-computed body; fall back to declared body.
        lib_box = library_body_box(cid, comp.get("pins", {}), lib_spec)

        declared = comp.get("body")
        if lib_box:
            # Warn if the declared body is smaller than the library body
            if declared:
                d_top    = int(declared["top-row"])
                d_bottom = int(declared["bottom-row"])
                d_lci    = col_index(str(declared["left-col"]).upper())
                d_rci    = col_index(str(declared["right-col"]).upper())
                l_top, l_bottom, l_lc, l_rc, _ = lib_box
                if (d_top > l_top or d_bottom < l_bottom
                        or d_lci > col_index(l_lc)
                        or d_rci < col_index(l_rc)):
                    errors.append(
                        f"BODY UNDERSPEC: '{cid}' declared body "
                        f"(rows {d_top}–{d_bottom}, cols "
                        f"{declared['left-col']}–{declared['right-col']}) is "
                        f"smaller than the library footprint "
                        f"(rows {l_top}–{l_bottom}, cols {l_lc}–{l_rc}). "
                        f"Update breadboard.yaml body to match the library."
                    )
            bodies.append(lib_box)
        elif declared:
            bodies.append((
                int(declared["top-row"]),
                int(declared["bottom-row"]),
                str(declared["left-col"]).upper(),
                str(declared["right-col"]).upper(),
                cid,
            ))

    # ── 1b. Build index of all declared component pins for pin: reference checks ─
    comp_pin_index: dict[str, set] = {}   # comp_id → {pin_name, ...}
    for comp in layout.get("components", []):
        cid = comp.get("id", "<unnamed>")
        comp_pin_index[cid] = set(comp.get("pins", {}).keys())
    for comp in layout.get("external_components", []):
        cid = comp.get("id", "<unnamed>")
        # External components use their connections dict as the pin set
        comp_pin_index[cid] = set(comp.get("connections", {}).keys())

    # ── 1c. Validate pin: wire endpoints reference real component pins ──────────
    for wire in layout.get("wires", []):
        label = wire.get("purpose", "unnamed wire")
        for side in ("from", "to"):
            raw = str(wire.get(side, "")).strip()
            if not raw.startswith("pin:"):
                continue
            # Expected format: pin:component_id.pin_name
            rest = raw[4:]  # strip "pin:"
            if "." not in rest:
                errors.append(
                    f"INVALID PIN REF: '{raw}' ({side} of '{label}') — "
                    f"expected format pin:component_id.pin_name"
                )
                continue
            cid, pin_name = rest.split(".", 1)
            if cid not in comp_pin_index:
                errors.append(
                    f"UNKNOWN COMPONENT: '{raw}' ({side} of '{label}') — "
                    f"component '{cid}' is not declared in components or external_components"
                )
            elif pin_name not in comp_pin_index[cid]:
                errors.append(
                    f"UNKNOWN PIN: '{raw}' ({side} of '{label}') — "
                    f"'{pin_name}' is not a declared pin of component '{cid}'"
                )

    # ── 1d. Check pin: wires against header_info.left.tap_method ─────────────
    # A wire using "pin:comp.PIN" claims it can physically attach a female jumper
    # to a header pin above the PCB.  This is only valid when the component's
    # parts_library entry declares tap_method == "female_jumper".
    for wire in layout.get("wires", []):
        label = wire.get("purpose", "unnamed wire")
        for side in ("from", "to"):
            raw = str(wire.get(side, "")).strip()
            if not raw.startswith("pin:"):
                continue
            cid = raw[4:].split(".")[0]
            ctype = next((c.get("type","") for c in layout.get("components",[])
                          if c.get("id") == cid), None)
            if not ctype:
                continue
            tap = (library.get(ctype, {})
                   .get("header_info", {}).get("left", {}).get("tap_method", "none"))
            if tap != "female_jumper":
                errors.append(
                    f"PHYSICAL CONSTRAINT: '{label}' uses '{raw}' but "
                    f"{ctype} has header_info.left.tap_method='{tap}' — "
                    f"female jumper attachment is not physically feasible for this "
                    f"board variant. Reassign to a right-header GPIO or use P2P mode."
                )

    # ── 1e. Check that each used power rail has at least one source wire ──────
    # A "source wire" is one where `to == rail-X` and `from` is in the same
    # breadboard row-half as an ESP32 pin of the matching polarity (GND or 3V3).
    # This correctly identifies right-header GND taps (e.g. J1 → I1=GND.2)
    # as valid GND sources while flagging circuits where rail-plus has no source
    # because the 3V3 left-header pins cannot be tapped (tap_method='none').

    # Build (row, half) sets from ESP32 pin positions in the occupied dict.
    # "half" = "L" for left (A–E), "R" for right (F–J).
    esp32_gnd_taps:  set[tuple] = set()
    esp32_vcc_taps:  set[tuple] = set()
    for comp in layout.get("components", []):
        if comp.get("type") != "board-esp32-s3-devkitc-1":
            continue
        for pin_name, raw_hole in comp.get("pins", {}).items():
            parsed = parse_hole(str(raw_hole))
            if not parsed:
                continue
            col, row = parsed
            half = "L" if col in LEFT_HALF else "R"
            pnu = pin_name.upper()
            if "GND" in pnu:
                esp32_gnd_taps.add((row, half))
            elif "3V3" in pnu or "5V" in pnu:
                esp32_vcc_taps.add((row, half))

    def is_esp32_tap(hole_str: str, tap_set: set) -> bool:
        """Return True if hole_str is in the same row-half as an ESP32 power pin."""
        p = parse_hole(hole_str)
        if not p:
            return False
        col, row = p
        half = "L" if col in LEFT_HALF else "R"
        return (row, half) in tap_set

    for rail_key, rail_alts, vcc_rail in [
        ("rail-plus",  ("rail-plus", "rail+"),  True),
        ("rail-minus", ("rail-minus", "rail-"), False),
    ]:
        tap_set = esp32_vcc_taps if vcc_rail else esp32_gnd_taps
        rail_wires = [w for w in layout.get("wires", [])
                      if str(w.get("from","")).strip() in rail_alts or
                         str(w.get("to","")).strip() in rail_alts]
        if not rail_wires:
            continue   # rail not referenced — no problem
        # A source wire: "to" is the rail AND "from" is an ESP32 power-pin tap
        # OR a pin: endpoint (which check 1d will separately validate).
        source_wires = [
            w for w in rail_wires
            if str(w.get("to","")).strip() in rail_alts and (
                str(w.get("from","")).startswith("pin:") or
                is_esp32_tap(str(w.get("from","")).strip(), tap_set)
            )
        ]
        if not source_wires:
            if vcc_rail:
                detail = (
                    "The ESP32-S3's 3V3 pins (A1, A2) are on the left header where "
                    "tap_method='none' — they cannot be tapped from the breadboard. "
                    "Connect an external 3.3 V supply to rail-plus, or switch to P2P mode."
                )
            else:
                detail = (
                    "Add a wire from a col-J hole adjacent to an ESP32 right-header "
                    "GND pin (e.g. J1 for GND.2, J21 for GND.3, J22 for GND.4)."
                )
            errors.append(
                f"POWER RAIL UNCONNECTED: '{rail_key}' is used by "
                f"{len(rail_wires)} wire(s) but has no source wire. {detail}"
            )

    # ── 2. Check every wire endpoint ──────────────────────────────────────────
    for wire in layout.get("wires", []):
        label = wire.get("purpose", "unnamed wire")
        for side in ("from", "to"):
            raw = str(wire.get(side, ""))
            if not raw or parse_hole(raw) is None:
                continue   # rail or external endpoint — skip
            col, row = parse_hole(raw)
            key = f"{col}{row}"
            if key in occupied:
                errors.append(
                    f"WIRE IN OCCUPIED HOLE: {key} ({side} of '{label}') "
                    f"is already used by {occupied[key]}"
                )

    # ── 2b. Check wire endpoints inside component body zones ──────────────────
    # A wire endpoint may not land inside a component's PCB body even if the
    # hole is not listed as occupied — the physical body blocks access.
    for wire in layout.get("wires", []):
        label = wire.get("purpose", "unnamed wire")
        for side in ("from", "to"):
            raw = str(wire.get(side, ""))
            if not raw or parse_hole(raw) is None:
                continue
            col, row = parse_hole(raw)
            col_idx = col_index(col)
            key = f"{col}{row}"
            if key in occupied:
                continue  # already reported by check 2 if it's a conflict
            for body in bodies:
                t, b_row, lc, rc, comp_id = body
                if (t <= row <= b_row and
                        col_index(lc) <= col_idx <= col_index(rc)):
                    errors.append(
                        f"WIRE IN BODY ZONE: {key} ({side} of '{label}') "
                        f"is inside the physical body of '{comp_id}' "
                        f"(rows {t}–{b_row}, cols {lc}–{rc}) — "
                        f"this hole is physically inaccessible"
                    )
                    break

    # ── 2c. Check component pins inside foreign component body zones ───────────
    # A component's pin must not fall inside another component's PCB body.
    for comp in layout.get("components", []):
        cid = comp.get("id", "<unnamed>")
        for pin_name, raw_hole in comp.get("pins", {}).items():
            parsed = parse_hole(str(raw_hole))
            if parsed is None:
                continue
            col, row = parsed
            col_idx = col_index(col)
            for body in bodies:
                t, b_row, lc, rc, body_id = body
                if body_id == cid:
                    continue  # own body — pins are inside it by definition
                if (t <= row <= b_row and
                        col_index(lc) <= col_idx <= col_index(rc)):
                    errors.append(
                        f"PIN IN FOREIGN BODY: {cid}.{pin_name} at "
                        f"{col}{row} is inside the body of '{body_id}' "
                        f"(rows {t}–{b_row}, cols {lc}–{rc})"
                    )
                    break

    # ── 3. Check component body overlaps ──────────────────────────────────────
    for i, b1 in enumerate(bodies):
        for b2 in bodies[i + 1:]:
            t1, bo1, lc1, rc1, id1 = b1
            t2, bo2, lc2, rc2, id2 = b2
            row_overlap = not (bo1 < t2 or bo2 < t1)
            col_overlap = not (
                col_index(rc1) < col_index(lc2) or
                col_index(rc2) < col_index(lc1)
            )
            if row_overlap and col_overlap:
                errors.append(
                    f"BODY OVERLAP: '{id1}' (rows {t1}–{bo1}, "
                    f"cols {lc1}–{rc1}) physically overlaps "
                    f"'{id2}' (rows {t2}–{bo2}, cols {lc2}–{rc2})"
                )

    # ── 4. Check breadboard capacity ──────────────────────────────────────────
    bb = layout.get("breadboard", {})
    max_rows = int(bb.get("rows", DEFAULT_MAX_ROWS))

    high_water = 0
    for comp in layout.get("components", []):
        body = comp.get("body")
        if body:
            high_water = max(high_water, int(body["bottom-row"]))
    for wire in layout.get("wires", []):
        for side in ("from", "to"):
            parsed = parse_hole(str(wire.get(side, "")))
            if parsed:
                high_water = max(high_water, parsed[1])

    if high_water > max_rows:
        errors.append(
            f"BREADBOARD TOO SMALL: layout needs row {high_water}, "
            f"but breadboard only has {max_rows} rows"
        )

    return errors


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: breadboard_validator.py <breadboard.yaml> [parts_library.yaml]",
              file=sys.stderr)
        sys.exit(2)

    breadboard_path = args[0]
    library_path    = args[1] if len(args) > 1 else None

    errors = validate(breadboard_path, library_path)

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"\n{len(errors)} violation(s) — layout is NOT buildable as written.")
        sys.exit(1)

    print("OK — layout is valid. No physical constraint violations found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
