#!/usr/bin/env python3
"""
Breadboard physical constraint validator.

Checks a breadboard.yaml layout for three classes of error:
  1. HOLE CONFLICT    — two component pins assigned to the same hole
  2. WIRE IN OCCUPIED HOLE — a jumper wire endpoint is in a hole already taken by a pin
  3. BODY OVERLAP     — a component's PCB body region physically overlaps another's
  4. BREADBOARD TOO SMALL — layout exceeds the declared row count

Usage:
    python3 breadboard_validator.py breadboard.yaml
Exit 0 = valid.  Exit 1 = one or more violations found.
"""

import sys
import yaml

COLUMNS = list("ABCDEFGHIJ")
LEFT_HALF  = set("ABCDE")
RIGHT_HALF = set("FGHIJ")
DEFAULT_MAX_ROWS = 63
RAIL_PREFIXES = ("rail-", "rail+", "rail_")


def col_index(col: str) -> int:
    return COLUMNS.index(col.upper())


def parse_hole(hole: str):
    """Parse 'A1', 'J22', etc.  Returns (col_str, row_int) or None for rails/invalid."""
    if not hole:
        return None
    s = str(hole).strip()
    if s.lower().startswith(RAIL_PREFIXES):
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


def validate(path: str) -> list[str]:
    with open(path) as f:
        layout = yaml.safe_load(f)

    errors: list[str] = []
    occupied: dict[str, str] = {}          # "A1" → "esp32.3V3.1"
    bodies:   list[tuple] = []             # (top, bottom, lc, rc, id)

    # ── 1. Register component pins and body bounding boxes ──────────────────
    for comp in layout.get("components", []):
        cid = comp.get("id", "<unnamed>")

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

        body = comp.get("body")
        if body:
            bodies.append((
                int(body["top-row"]),
                int(body["bottom-row"]),
                str(body["left-col"]).upper(),
                str(body["right-col"]).upper(),
                cid,
            ))

    # ── 2. Check every wire endpoint ────────────────────────────────────────
    for wire in layout.get("wires", []):
        label = wire.get("purpose", "unnamed wire")
        for side in ("from", "to"):
            raw = str(wire.get(side, ""))
            if not raw or raw.lower().startswith(RAIL_PREFIXES):
                continue
            parsed = parse_hole(raw)
            if parsed is None:
                errors.append(f"INVALID WIRE HOLE: {side}='{raw}' in '{label}'")
                continue
            col, row = parsed
            key = f"{col}{row}"
            if key in occupied:
                errors.append(
                    f"WIRE IN OCCUPIED HOLE: {key} ({side} of '{label}') "
                    f"is already used by {occupied[key]}"
                )

    # ── 3. Check component body overlaps ────────────────────────────────────
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
                    f"BODY OVERLAP: '{id1}' (rows {t1}–{bo1}, cols {lc1}–{rc1}) "
                    f"physically overlaps '{id2}' (rows {t2}–{bo2}, cols {lc2}–{rc2})"
                )

    # ── 4. Check breadboard capacity ────────────────────────────────────────
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


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: breadboard_validator.py <breadboard.yaml>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    errors = validate(path)

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"\n{len(errors)} violation(s) — layout is NOT buildable as written.")
        sys.exit(1)

    print("OK — layout is valid. No physical constraint violations found.")
    sys.exit(0)


if __name__ == "__main__":
    main()
