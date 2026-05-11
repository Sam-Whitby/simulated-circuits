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
EXTERNAL_PREFIXES = ("external:", "ext:")


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
    # Auto-discover alongside the breadboard file
    auto = os.path.join(os.path.dirname(os.path.abspath(breadboard_path)),
                        "parts_library.yaml")
    candidates.append(auto)

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
