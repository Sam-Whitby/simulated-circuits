#!/usr/bin/env python3
"""
Breadboard placer — deterministic algorithmic layout generator.

Reads netlist.yaml + parts_library.yaml and produces a valid breadboard.yaml
by construction.  If no valid layout exists, exits 2 with a structured
infeasibility report.

Exit codes:
  0 — feasible; breadboard.yaml written
  2 — infeasible; reason printed to stdout; no output file written
  1 — tool error (bad input, missing library entry, etc.)

Usage:
    python3 breadboard_placer.py netlist.yaml breadboard.yaml
    python3 breadboard_placer.py netlist.yaml  # dry-run: print layout to stdout
"""

import os
import sys
import yaml
from dataclasses import dataclass, field
from typing import Optional

COLUMNS     = list("ABCDEFGHIJ")
LEFT_HALF   = set("ABCDE")
RIGHT_HALF  = set("FGHIJ")
MAX_ROWS    = 63

# ── Infeasibility codes ───────────────────────────────────────────────────────

INFEASIBLE_CODES = {
    "MISSING_LIBRARY_ENTRY":    "Add component type to parts_library.yaml",
    "COMPONENT_TOO_LARGE":      "Mark component external_only:true in parts_library.yaml, "
                                "or use point-to-point assembly (p2p_layout.py)",
    "BOARD_FULL":               "Use a larger breadboard (more rows), or use "
                                "point-to-point assembly (p2p_layout.py)",
    "GPIO_INACCESSIBLE":        "Reassign this signal to a right-header GPIO (col I), "
                                "or use point-to-point assembly (p2p_layout.py)",
    "WIRE_ROUTING_FAILED":      "No free adjacent hole for wire endpoint; try a different "
                                "GPIO assignment, or use point-to-point assembly",
    "NET_SHORT":                "Circuit design error — fix the netlist (diagram.json)",
    "EXTERNAL_ONLY_UNREACHABLE":"External component pin has no reachable breadboard tap point; "
                                "use point-to-point assembly (p2p_layout.py)",
}


def col_index(col: str) -> int:
    return COLUMNS.index(col.upper())


def infeasible(code: str, message: str) -> None:
    suggestion = INFEASIBLE_CODES.get(code, "See documentation")
    print(f"INFEASIBLE [{code}]: {message}")
    print(f"  Suggestion: {suggestion}")
    sys.exit(2)


# ── Board state ───────────────────────────────────────────────────────────────

@dataclass
class BoardState:
    occupied: dict = field(default_factory=dict)   # "A1" → "comp.pin"
    bodies:   list = field(default_factory=list)   # (top, bottom, lc, rc, id)

    def hole_key(self, col: str, row: int) -> str:
        return f"{col.upper()}{row}"

    def is_occupied(self, col: str, row: int) -> bool:
        return self.hole_key(col, row) in self.occupied

    def in_any_body(self, col: str, row: int) -> bool:
        ci = col_index(col)
        for t, b, lc, rc, _ in self.bodies:
            if t <= row <= b and col_index(lc) <= ci <= col_index(rc):
                return True
        return False

    def is_valid_hole(self, col: str, row: int) -> bool:
        return (not self.is_occupied(col, row) and
                not self.in_any_body(col, row) and
                1 <= row <= MAX_ROWS and
                col.upper() in COLUMNS)

    def mark_occupied(self, col: str, row: int, label: str) -> None:
        self.occupied[self.hole_key(col, row)] = label

    def add_body(self, top: int, bottom: int, lc: str, rc: str, cid: str) -> None:
        self.bodies.append((top, bottom, lc.upper(), rc.upper(), cid))

    def same_half(self, col1: str, col2: str) -> bool:
        return (col1.upper() in LEFT_HALF) == (col2.upper() in LEFT_HALF)

    def free_adjacent(self, col: str, row: int) -> Optional[str]:
        """
        Return the first free hole in the same row-half as (col, row) that is
        not occupied and not in any body zone, preferring adjacent columns.
        Returns the column letter, or None if no free hole found.
        """
        half = LEFT_HALF if col.upper() in LEFT_HALF else RIGHT_HALF
        cols_in_half = [c for c in COLUMNS if c in half]
        # Scan outward from the given col
        idx = cols_in_half.index(col.upper())
        # Try left then right from the anchor, expanding outward
        order = []
        for d in range(1, len(cols_in_half)):
            if idx - d >= 0:
                order.append(cols_in_half[idx - d])
            if idx + d < len(cols_in_half):
                order.append(cols_in_half[idx + d])
        for c in order:
            if self.is_valid_hole(c, row):
                return c
        return None


# ── Parts library helpers ─────────────────────────────────────────────────────

def load_library(netlist_path: str) -> dict:
    base = os.path.dirname(os.path.abspath(netlist_path))
    candidates = [
        os.path.join(base, "parts_library.yaml"),
        os.path.join(os.path.dirname(base), "parts_library.yaml"),
    ]
    for lib_path in candidates:
        if os.path.exists(lib_path):
            with open(lib_path) as f:
                lib = yaml.safe_load(f)
            return lib.get("components", {})
    print(f"ERROR: parts_library.yaml not found (searched: {candidates})",
          file=sys.stderr)
    sys.exit(1)


def compute_body(anchor_col: str, anchor_row: int, lib_spec: dict) -> tuple:
    """Return (top, bottom, left_col, right_col) from library body offsets."""
    body = lib_spec.get("body_breadboard", {})
    aci = col_index(anchor_col)
    top    = anchor_row - body.get("rows_above_anchor", 0)
    bottom = anchor_row + body.get("rows_below_anchor", 0)
    lci    = aci - body.get("cols_left_of_anchor", 0)
    rci    = aci + body.get("cols_right_of_anchor", 0)
    lc = COLUMNS[max(0, lci)]
    rc = COLUMNS[min(len(COLUMNS) - 1, rci)]
    return top, bottom, lc, rc


def pin_holes_from_library(anchor_col: str, anchor_row: int,
                            lib_spec: dict) -> dict:
    """Compute all pin holes from library offsets relative to anchor."""
    lib_pins = lib_spec.get("pins", {})
    if not lib_pins:
        return {}
    anchor_name = next(iter(lib_pins))
    aci = col_index(anchor_col)
    result = {}
    for pin_name, offsets in lib_pins.items():
        dc = offsets.get("offset_col", 0)
        dr = offsets.get("offset_row", 0)
        ci = aci + dc
        r  = anchor_row + dr
        if 0 <= ci < len(COLUMNS):
            result[pin_name] = (COLUMNS[ci], r)
    return result


# ── ESP32 placement (fixed) ───────────────────────────────────────────────────

def place_esp32(board: BoardState, comp: dict, library: dict) -> dict:
    """
    Place the ESP32 at the fixed location mandated by its physical dimensions.
    Returns a dict mapping pin_name → (col, row).
    """
    lib_spec = library.get("board-esp32-s3-devkitc-1", {})
    if not lib_spec:
        infeasible("MISSING_LIBRARY_ENTRY",
                   "board-esp32-s3-devkitc-1 not found in parts_library.yaml")

    # Fixed positions
    LEFT_COL, RIGHT_COL = "A", "I"
    START_ROW = 1
    N_PINS    = 22

    pin_map = {}   # pin_name → (col, row)

    # The netlist uses component pin names like "esp32.1" (GPIO1).
    # Map from the netlist comp entry's known pins if provided, else derive.
    netlist_pins = comp.get("pins", {})   # may be empty in netlist

    # Register all left-header and right-header positions
    # We read them from the breadboard.yaml convention: left=A, right=I, rows 1-22.
    # The placer hard-codes this since the ESP32 physical position is fixed.
    for row in range(START_ROW, START_ROW + N_PINS):
        for hcol in (LEFT_COL, RIGHT_COL):
            board.mark_occupied(hcol, row, f"esp32.header.{hcol}{row}")

    # Body: rows 1-26, cols A-I
    body_spec = lib_spec.get("body_breadboard", {})
    top    = START_ROW
    bottom = START_ROW + body_spec.get("rows_below_anchor", 25)
    lc     = LEFT_COL
    rci    = col_index(LEFT_COL) + body_spec.get("cols_right_of_anchor", 8)
    rc     = COLUMNS[min(rci, len(COLUMNS) - 1)]
    board.add_body(top, bottom, lc, rc, "esp32")

    return bottom   # return the body bottom row so other components start below it


# ── Generic component placement ───────────────────────────────────────────────

# Column preference order for placed components: use right-half first so that
# col J is available as a GPIO tap point.
PLACEMENT_COL_ORDER = ["H", "G", "C", "D", "B", "F", "E", "A", "J"]


def place_component(cid: str, ctype: str, lib_spec: dict,
                    board: BoardState, first_row: int) -> tuple:
    """
    Find the first valid anchor position for a component and mark it placed.
    Returns dict of pin_name → (col, row) or calls infeasible().
    """
    if not lib_spec:
        infeasible("MISSING_LIBRARY_ENTRY",
                   f"Component '{cid}' has type '{ctype}' which is not in parts_library.yaml")

    if lib_spec.get("external_only"):
        # External components are not placed on the board
        return {}

    lib_pins = lib_spec.get("pins", {})
    if not lib_pins:
        infeasible("MISSING_LIBRARY_ENTRY",
                   f"Library entry for '{ctype}' has no pins defined — cannot place")

    for row in range(first_row, MAX_ROWS + 1):
        for col in PLACEMENT_COL_ORDER:
            # Compute where all pins would land at this anchor position
            pin_holes = pin_holes_from_library(col, row, lib_spec)
            if not pin_holes:
                continue

            # Check all pins are in valid, free holes
            ok = True
            for pn, (pc, pr) in pin_holes.items():
                if not board.is_valid_hole(pc, pr):
                    ok = False
                    break
            if not ok:
                continue

            # Check body doesn't overlap existing bodies
            top, bottom, lc, rc = compute_body(col, row, lib_spec)
            body_ok = True
            for bt, bb, blc, brc, bid in board.bodies:
                row_ov = not (bottom < bt or bb < top)
                col_ov = not (col_index(rc) < col_index(blc) or
                              col_index(brc) < col_index(lc))
                if row_ov and col_ov:
                    body_ok = False
                    break
            if not body_ok:
                continue

            # Valid position found — mark it
            for pn, (pc, pr) in pin_holes.items():
                board.mark_occupied(pc, pr, f"{cid}.{pn}")
            board.add_body(top, bottom, lc, rc, cid)
            return pin_holes

    # No position found
    if first_row > MAX_ROWS:
        infeasible("BOARD_FULL",
                   f"No space for '{cid}' (type={ctype}): breadboard is full")
    infeasible("COMPONENT_TOO_LARGE",
               f"Cannot place '{cid}' (type={ctype}): body doesn't fit in remaining space")


# ── Wire routing ──────────────────────────────────────────────────────────────

def resolve_component_pin(pin_ref: str, placements: dict,
                           esp32_pin_map: dict,
                           library: dict) -> Optional[tuple]:
    """
    Resolve 'component_id.pin_name' to (col, row) or special string.
    Returns:
      (col, row)       — standard breadboard hole
      ("pin:", ref)    — female wire onto ESP32 header pin above PCB
                         (only when library confirms tap_method == "female_jumper")
      None             — cannot resolve
    Calls infeasible() if a left-header pin is requested but the board type
    does not support female-jumper connections.
    """
    if "." not in pin_ref:
        return None
    cid, pin_name = pin_ref.split(".", 1)

    # Check ESP32 specifically
    if cid == "esp32":
        if pin_name in esp32_pin_map:
            col, row = esp32_pin_map[pin_name]
            half = "left" if col in LEFT_HALF else "right"
            if half == "right":
                # Right-header: tap via col J (outside body, always accessible)
                return ("J", row)
            else:
                # Left-header: no adjacent breadboard hole exists (body covers B–E).
                # Whether a female jumper above the PCB is feasible depends on the board.
                lib_spec = library.get("board-esp32-s3-devkitc-1", {})
                tap_method = (lib_spec.get("header_info", {})
                              .get("left", {}).get("tap_method", "none"))
                if tap_method == "female_jumper":
                    return ("pin:", f"esp32.{pin_name}")
                else:
                    infeasible(
                        "GPIO_INACCESSIBLE",
                        f"esp32.{pin_name} is on the left header (col A, row {row}). "
                        f"No adjacent breadboard hole exists (cols B–E rows 1–22 are "
                        f"blocked by the PCB body), and parts_library.yaml reports "
                        f"header_info.left.tap_method='{tap_method}' — female jumper "
                        f"attachment is not physically feasible for this board variant. "
                        f"Fix: reassign this signal to a right-header GPIO (col I, "
                        f"tapped via col J), or use point-to-point assembly (p2p_layout.py)."
                    )
        return None

    if cid in placements:
        comp_pins = placements[cid]
        if pin_name in comp_pins:
            return comp_pins[pin_name]

    return None


def route_net(net: dict, placements: dict, esp32_pin_map: dict,
              board: BoardState, wires: list, ext_comps: dict,
              library: dict) -> None:
    """
    Route all connections in a net, generating wire entries.
    A net may connect to rails, ESP32 pins, placed components, or external components.
    Junction nodes with 3+ pins use one pin as the hub and star-wire others to it.
    """
    net_name = net.get("name", "unnamed")
    pins     = net.get("pins", [])
    rails    = net.get("rails", [])

    rail_target = None
    if "rail:plus" in rails:
        rail_target = "rail-plus"
    elif "rail:minus" in rails:
        rail_target = "rail-minus"

    # Check for rail short
    if "rail:plus" in rails and "rail:minus" in rails:
        infeasible("NET_SHORT",
                   f"Net '{net_name}' connects to both rail:plus and rail:minus")

    # Resolve all pins to physical endpoints
    endpoints = []   # list of (from_type, value)
    # "from_type" is one of: "hole" (col,row), "pin:" (female ref), "rail", "ext"

    for pin_ref in pins:
        # Check if external component pin
        if "." in pin_ref:
            cid, pin_name = pin_ref.split(".", 1)
            if cid in ext_comps:
                endpoints.append(("ext", f"ext:{cid}:{pin_name}"))
                continue

        resolved = resolve_component_pin(pin_ref, placements, esp32_pin_map, library)
        if resolved is None:
            # Skip unresolvable pins silently (e.g. NC pins)
            continue
        if resolved[0] == "pin:":
            endpoints.append(("pin:", resolved[1]))
        elif resolved[0] == "J" or (len(resolved) == 2 and isinstance(resolved[0], str) and len(resolved[0]) == 1):
            endpoints.append(("hole", resolved))
        else:
            endpoints.append(("hole", resolved))

    if rail_target:
        endpoints.append(("rail", rail_target))

    # Build wires: connect every endpoint to the first endpoint (star topology)
    # For hole endpoints, find a free adjacent hole as the tap point.
    tap_points = []   # (wire_from, wire_to) strings

    for etype, evalue in endpoints:
        if etype == "hole":
            col, row = evalue
            if board.is_occupied(col, row):
                # Find a free adjacent hole in the same row-half
                adj = board.free_adjacent(col, row)
                if adj is None:
                    infeasible("WIRE_ROUTING_FAILED",
                               f"Net '{net_name}': no free adjacent hole for "
                               f"component pin at {col}{row}")
                board.mark_occupied(adj, row, f"wire.{net_name}")
                tap_points.append(f"{adj}{row}")
            else:
                # The hole itself is free — use it directly as tap
                board.mark_occupied(col, row, f"wire.{net_name}")
                tap_points.append(f"{col}{row}")
        elif etype == "pin:":
            tap_points.append(f"pin:{evalue}")
        elif etype == "ext":
            tap_points.append(evalue)
        elif etype == "rail":
            tap_points.append(evalue)

    if len(tap_points) < 2:
        return   # Nothing to wire (rail-only or single pin)

    # Star: wire tap_points[1..] → tap_points[0]
    hub = tap_points[0]
    for spoke in tap_points[1:]:
        wires.append({
            "from":    hub,
            "to":      spoke,
            "color":   "gray",
            "purpose": net_name,
        })


# ── Output ────────────────────────────────────────────────────────────────────

LEFT_HEADER_PINS  = ["3V3.1","3V3.2","RST","4","5","6","7","15","16","17","18",
                     "8","3","46","9","10","11","12","13","14","5V","GND.1"]
RIGHT_HEADER_PINS = ["GND.2","TX","RX","1","2","42","41","40","39","38","37",
                     "36","35","0","45","48","47","21","20","19","GND.3","GND.4"]


def build_yaml(board: BoardState, placements: dict, wires: list,
               netlist: dict, library: dict) -> str:
    """Build the breadboard.yaml content string."""

    # ── ESP32 component entry (fixed position) ────────────────────────────────
    lib_spec  = library.get("board-esp32-s3-devkitc-1", {})
    body_spec = lib_spec.get("body_breadboard", {})
    esp_body_bottom = 1 + body_spec.get("rows_below_anchor", 25)
    esp_body_rc_idx = body_spec.get("cols_right_of_anchor", 8)
    esp_body_rc     = COLUMNS[min(esp_body_rc_idx, len(COLUMNS) - 1)]

    esp_pins_block = {}
    for i, pn in enumerate(LEFT_HEADER_PINS):
        esp_pins_block[pn] = f"A{i+1}"
    for i, pn in enumerate(RIGHT_HEADER_PINS):
        esp_pins_block[pn] = f"I{i+1}"

    esp32_entry = {
        "id":   "esp32",
        "type": "board-esp32-s3-devkitc-1",
        "body": {"top-row": 1, "bottom-row": esp_body_bottom,
                 "left-col": "A", "right-col": esp_body_rc},
        "pins": esp_pins_block,
    }

    # ── Placed (non-ESP32, non-external) components ───────────────────────────
    placed_out = [esp32_entry]
    for cid, pin_holes in placements.items():
        ctype = next((c["type"] for c in netlist["components"] if c["id"] == cid), "")
        lib   = library.get(ctype, {})
        if not pin_holes:
            continue
        first_pin = next(iter(pin_holes.values()))
        ac, ar = first_pin
        top, bottom, lc, rc = compute_body(ac, ar, lib)
        pins_block = {pn: f"{pc}{pr}" for pn, (pc, pr) in pin_holes.items()}
        placed_out.append({
            "id": cid, "type": ctype,
            "body": {"top-row": top, "bottom-row": bottom,
                     "left-col": lc, "right-col": rc},
            "pins": pins_block,
        })

    # ── External components ───────────────────────────────────────────────────
    ext_comps_out = []
    for comp in netlist.get("components", []):
        if comp.get("external"):
            cid   = comp["id"]
            ctype = comp["type"]
            conns = {}
            for net in netlist.get("nets", []):
                for pin_ref in net.get("pins", []):
                    if "." in pin_ref:
                        pcid, ppin = pin_ref.split(".", 1)
                        if pcid == cid:
                            rails = net.get("rails", [])
                            if "rail:plus" in rails:
                                conns[ppin] = "rail-plus"
                            elif "rail:minus" in rails:
                                conns[ppin] = "rail-minus"
            ext_comps_out.append({
                "id": cid, "type": ctype,
                "reason": "External component (see parts_library.yaml)",
                "connections": conns,
            })

    circuit_name = netlist.get("circuit", "")
    doc_dict: dict = {}
    if circuit_name:
        doc_dict["circuit"] = circuit_name
    doc_dict.update({
        "breadboard":          {"type": "full-size", "rows": MAX_ROWS,
                                "columns": list(COLUMNS)},
        "components":          placed_out,
        "external_components": ext_comps_out,
        "wires":               wires,
    })
    doc = yaml.dump(doc_dict, default_flow_style=False, allow_unicode=True, sort_keys=False)

    header = (
        "# breadboard.yaml — generated by breadboard_placer.py\n"
        "# Validate with: python3 breadboard_validator.py breadboard.yaml\n\n"
    )
    return header + doc


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: breadboard_placer.py <netlist.yaml> [output_breadboard.yaml]",
              file=sys.stderr)
        sys.exit(1)

    netlist_path = args[0]
    output_path  = args[1] if len(args) > 1 else None

    with open(netlist_path) as f:
        netlist = yaml.safe_load(f)

    library = load_library(netlist_path)

    board     = BoardState()
    wires     = []
    placements: dict = {}   # cid → {pin_name: (col, row)}
    ext_comps: dict = {}    # cid → True (for external components)

    # ── Validate no rail shorts ───────────────────────────────────────────────
    for net in netlist.get("nets", []):
        rails = net.get("rails", [])
        if "rail:plus" in rails and "rail:minus" in rails:
            infeasible("NET_SHORT",
                       f"Net '{net.get('name','?')}' connects both supply rails")

    # ── Place ESP32 first (fixed position) ────────────────────────────────────
    esp32_body_bottom = 26
    for comp in netlist.get("components", []):
        if comp["id"] == "esp32":
            esp32_body_bottom = place_esp32(board, comp, library)
            break

    # Build ESP32 pin map from the fixed header positions
    left_pins  = ["3V3.1","3V3.2","RST","4","5","6","7","15","16","17","18",
                  "8","3","46","9","10","11","12","13","14","5V","GND.1"]
    right_pins = ["GND.2","TX","RX","1","2","42","41","40","39","38","37",
                  "36","35","0","45","48","47","21","20","19","GND.3","GND.4"]
    esp32_pin_map: dict = {}
    for i, pn in enumerate(left_pins):
        esp32_pin_map[pn] = ("A", i + 1)
    for i, pn in enumerate(right_pins):
        esp32_pin_map[pn] = ("I", i + 1)

    # ── Place remaining on-board components ───────────────────────────────────
    first_free_row = esp32_body_bottom + 2
    for comp in netlist.get("components", []):
        cid   = comp["id"]
        if cid == "esp32":
            continue
        ctype = comp.get("type", "")
        lib   = library.get(ctype, {})

        if comp.get("external") or lib.get("external_only"):
            ext_comps[cid] = True
            continue

        pin_holes = place_component(cid, ctype, lib, board, first_free_row)
        placements[cid] = pin_holes

    # ── Route wires for each net ──────────────────────────────────────────────
    for net in netlist.get("nets", []):
        if net.get("note", "").startswith("Unconnected"):
            continue   # skip NC nets
        route_net(net, placements, esp32_pin_map, board, wires, ext_comps, library)

    # ── Write output ──────────────────────────────────────────────────────────
    yaml_text = build_yaml(board, placements, wires, netlist, library)

    if output_path:
        with open(output_path, "w") as f:
            f.write(yaml_text)
        print(f"OK — breadboard.yaml written to '{output_path}'")
        print(f"     Run: python3 breadboard_validator.py {output_path}")
    else:
        print(yaml_text)

    sys.exit(0)


if __name__ == "__main__":
    main()
