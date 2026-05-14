#!/usr/bin/env python3
"""
Point-to-point (P2P) wiring layout generator.

Reads netlist.yaml and produces pointtopoint.yaml — a flat list of explicit
wire connections between component pins.  No breadboard is involved.

P2P assembly: components sit on a flat non-conductive surface.  Connections
are made with individual jumper wires:
  • Female-to-male wires connect to MCU header pins directly (no breadboard).
  • Small passives (resistors, LDRs) are wired lead-to-lead at junction nodes.
  • Junction nodes (3+ pins on one net) are expressed as a daisy-chain.

P2P layout is ALWAYS feasible for any valid netlist (there are no body zones,
hole conflicts, or breadboard capacity limits).  The only check performed is
that the netlist contains no rail-to-rail short circuits.

Exit codes:
  0 — success; pointtopoint.yaml written (or printed to stdout)
  1 — tool error (bad input)
  2 — infeasible netlist (rail short detected)

Usage:
    python3 p2p_layout.py netlist.yaml pointtopoint.yaml
    python3 p2p_layout.py netlist.yaml   # dry-run: print to stdout
"""

import os
import sys
import yaml

WIRE_COLOURS = ["red", "black", "yellow", "blue", "green", "orange",
                "purple", "white", "cyan", "gray"]

# Human-readable pin descriptions for common ESP32-S3-DevKitC-1 pins.
# Helps the assembly generator produce clear instructions.
ESP32_PIN_LABELS = {
    "3V3.1":  "3V3 (left header, pin 1 — top-left)",
    "3V3.2":  "3V3 (left header, pin 2)",
    "GND.1":  "GND (left header, pin 22 — bottom-left)",
    "GND.2":  "GND (right header, pin 1 — top-right)",
    "GND.3":  "GND (right header, pin 21)",
    "GND.4":  "GND (right header, pin 22 — bottom-right)",
    "1":      "GPIO1 (right header, pin 4)",
    "2":      "GPIO2 (right header, pin 5)",
    "38":     "GPIO38 (right header, pin 10)",
    "39":     "GPIO39 (right header, pin 9)",
    "40":     "GPIO40 (right header, pin 8)",
    "41":     "GPIO41 (right header, pin 7)",
    "42":     "GPIO42 (right header, pin 6)",
}


def colour_for(net_name: str, index: int) -> str:
    name_hints = {
        "VCC": "red", "3V3": "red", "PLUS": "red", "POWER": "red",
        "GND": "black", "MINUS": "black", "GROUND": "black",
        "RS":  "blue",
        "EN":  "purple", "LCD_E": "purple",
        "D4":  "orange", "LCD_D4": "orange",
        "D5":  "yellow", "LCD_D5": "yellow",
        "D6":  "green",  "LCD_D6": "green",
        "D7":  "white",  "LCD_D7": "white",
        "ADC": "yellow", "JUNCTION": "yellow",
    }
    for hint, colour in name_hints.items():
        if hint.upper() in net_name.upper():
            return colour
    return WIRE_COLOURS[index % len(WIRE_COLOURS)]


def pin_label(comp_id: str, pin_name: str, comps_by_id: dict) -> str:
    ctype = comps_by_id.get(comp_id, {}).get("type", "")
    if comp_id == "esp32":
        label = ESP32_PIN_LABELS.get(pin_name, f"GPIO{pin_name} (ESP32 header)")
        return f"esp32.{label}"
    return f"{comp_id}.{pin_name}"


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: p2p_layout.py <netlist.yaml> [output_pointtopoint.yaml]",
              file=sys.stderr)
        sys.exit(1)

    netlist_path = args[0]
    output_path  = args[1] if len(args) > 1 else None

    with open(netlist_path) as f:
        netlist = yaml.safe_load(f)

    comps_by_id = {c["id"]: c for c in netlist.get("components", [])}

    wires   = []
    net_idx = 0

    for net in netlist.get("nets", []):
        net_name = net.get("name", f"net_{net_idx}")
        rails    = net.get("rails", [])
        pins     = net.get("pins", [])

        # Rail short check
        if "rail:plus" in rails and "rail:minus" in rails:
            print(f"INFEASIBLE [NET_SHORT]: Net '{net_name}' connects both supply rails",
                  file=sys.stderr)
            print("  Suggestion: Fix the circuit design (diagram.json / netlist.yaml)",
                  file=sys.stderr)
            sys.exit(2)

        # Skip NC nets
        if net.get("note", "").startswith("Unconnected"):
            continue

        colour = colour_for(net_name, net_idx)

        # Build flat endpoint list
        endpoints = []
        for pin_ref in pins:
            if "." in pin_ref:
                cid, ppin = pin_ref.split(".", 1)
                endpoints.append(("component", cid, ppin))

        if "rail:plus" in rails:
            endpoints.append(("rail", "plus", "+3V3 supply"))
        if "rail:minus" in rails:
            endpoints.append(("rail", "minus", "GND"))

        if len(endpoints) < 2:
            net_idx += 1
            continue

        # Daisy-chain: hub = endpoints[0], spokes = endpoints[1:]
        hub = endpoints[0]
        for spoke in endpoints[1:]:
            def ep_str(ep):
                if ep[0] == "component":
                    return pin_label(ep[1], ep[2], comps_by_id)
                else:
                    return f"rail:{ep[1]}"

            def ep_note(ep):
                if ep[0] == "component":
                    cid, ppin = ep[1], ep[2]
                    ctype = comps_by_id.get(cid, {}).get("type", "")
                    if cid == "esp32":
                        return (f"female end onto ESP32 header pin: "
                                f"{ESP32_PIN_LABELS.get(ppin, ppin)}")
                    if "external" in comps_by_id.get(cid, {}):
                        return f"{cid} external — connect to {ppin} header pin"
                    return f"{cid} lead '{ppin}'"
                elif ep[1] == "plus":
                    return "+3V3 supply terminal"
                else:
                    return "GND terminal"

            wires.append({
                "from":       ep_str(hub),
                "to":         ep_str(spoke),
                "from_note":  ep_note(hub),
                "to_note":    ep_note(spoke),
                "color":      colour,
                "net":        net_name,
                "purpose":    net.get("note", net_name),
            })

        net_idx += 1

    output = {
        "assembly_mode": "point-to-point",
        "circuit":       netlist.get("circuit", ""),
        "note": (
            "P2P assembly: no breadboard required. "
            "ESP32 sits on a non-conductive surface or is held by the USB cable. "
            "Connect each wire as listed. For junction nodes (a net with 3+ endpoints), "
            "twist the wire ends together or use a small solder blob."
        ),
        "wires": wires,
    }

    doc = yaml.dump(output, default_flow_style=False, allow_unicode=True, sort_keys=False)
    header = (
        "# pointtopoint.yaml — generated by p2p_layout.py\n"
        "# Generate assembly instructions with:\n"
        "#   python3 assembly_generator.py --mode p2p pointtopoint.yaml assembly.md\n\n"
    )
    result = header + doc

    if output_path:
        with open(output_path, "w") as f:
            f.write(result)
        print(f"OK — pointtopoint.yaml written to '{output_path}'")
        print(f"     Run: python3 assembly_generator.py --mode p2p {output_path} assembly.md")
    else:
        print(result)

    sys.exit(0)


if __name__ == "__main__":
    main()
