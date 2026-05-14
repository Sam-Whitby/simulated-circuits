#!/usr/bin/env python3
"""
configure_firmware.py — Switch platformio.ini between Wokwi simulation and real hardware.

Usage (run from the directory containing platformio.ini, or any subdirectory):
    python3 configure_firmware.py hw       # Real hardware: remove sim flags, enable USB OTG
    python3 configure_firmware.py sim      # Wokwi simulation: restore simulation flags
    python3 configure_firmware.py status   # Show current mode and active flags

The script edits build_flags in platformio.ini in place.  All other content
(comments, lib_deps, monitor_speed, etc.) is preserved exactly.

Flag management rules:
  SIM_FLAGS  — present only in simulation mode: -DWOKWI_SIMULATION=1
  HW_FLAGS   — present only in hardware mode:   -DARDUINO_USB_MODE=0

  In hw mode: SIM_FLAGS are removed; HW_FLAGS are added only if SIM_FLAGS were
  present (avoids adding USB OTG flag to projects that don't need it).

  In sim mode: HW_FLAGS are removed; SIM_FLAGS are added only if HW_FLAGS were
  present (mirrors the hw→sim round-trip).

Exit codes: 0 = success, 1 = error.
"""

import os
import sys

SIM_FLAGS: set[str] = {"-DWOKWI_SIMULATION=1"}
HW_FLAGS:  set[str] = {"-DARDUINO_USB_MODE=0"}


# ── INI file parsing (line-by-line to preserve comments exactly) ─────────────

def _find_build_flags_section(lines: list[str]) -> tuple[int, int]:
    """Return (start, end) line indices for the build_flags key+continuation."""
    start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("build_flags") and "=" in stripped:
            start = i
        elif start is not None and i > start:
            # Continuation lines are indented or blank within a multi-line value.
            # A non-indented, non-empty line (that isn't blank) ends the section.
            if line[:1] not in (" ", "\t") and line.strip():
                return start, i
    if start is None:
        return -1, -1
    return start, len(lines)


def _extract_flags(lines: list[str], start: int, end: int) -> list[str]:
    """Return flag strings from a build_flags section (excluding comments)."""
    flags: list[str] = []
    for line in lines[start:end]:
        stripped = line.strip()
        if stripped.startswith("build_flags"):
            _, _, rest = stripped.partition("=")
            rest = rest.strip()
            if rest and not rest.startswith(";"):
                flags.append(rest)
        elif stripped and not stripped.startswith(";"):
            flags.append(stripped)
    return flags


def _build_section_lines(flags: list[str], indent: str = "    ") -> list[str]:
    """Render a build_flags section as a list of file lines."""
    out = ["build_flags =\n"]
    for f in flags:
        out.append(f"{indent}{f}\n")
    return out


# ── Core logic ────────────────────────────────────────────────────────────────

def find_ini(start: str = ".") -> str | None:
    """Search for platformio.ini in start dir, then its parent."""
    for d in [os.path.abspath(start), os.path.dirname(os.path.abspath(start))]:
        p = os.path.join(d, "platformio.ini")
        if os.path.exists(p):
            return p
    return None


def read_modify_write(ini_path: str, mode: str) -> None:
    with open(ini_path) as f:
        lines = f.readlines()

    start, end = _find_build_flags_section(lines)
    if start < 0:
        sys.exit(f"ERROR: no 'build_flags' found in {ini_path}")

    original = _extract_flags(lines, start, end)
    flags    = list(original)

    if mode == "hw":
        removed_sim = [f for f in flags if f in SIM_FLAGS]
        flags = [f for f in flags if f not in SIM_FLAGS]
        if removed_sim:
            for hf in HW_FLAGS:
                if hf not in flags:
                    flags.append(hf)
        label = "real hardware"

    else:  # sim
        removed_hw = [f for f in flags if f in HW_FLAGS]
        flags = [f for f in flags if f not in HW_FLAGS]
        if removed_hw:
            for sf in SIM_FLAGS:
                if sf not in flags:
                    flags.append(sf)
        label = "Wokwi simulation"

    if flags == original:
        print(f"Already configured for {label} — {ini_path} unchanged.")
        return

    new_lines = lines[:start] + _build_section_lines(flags) + lines[end:]
    with open(ini_path, "w") as f:
        f.writelines(new_lines)

    removed = [f for f in original if f not in flags]
    added   = [f for f in flags   if f not in original]
    print(f"Configured for {label}: {ini_path}")
    for f in removed:
        print(f"  Removed: {f}")
    for f in added:
        print(f"  Added:   {f}")


def show_status(ini_path: str) -> None:
    with open(ini_path) as f:
        lines = f.readlines()
    start, end = _find_build_flags_section(lines)
    if start < 0:
        print(f"No build_flags found in {ini_path}")
        return
    flags   = _extract_flags(lines, start, end)
    is_sim  = any(f in SIM_FLAGS for f in flags)
    is_hw   = any(f in HW_FLAGS  for f in flags)
    mode    = ("simulation" if is_sim and not is_hw else
               "hardware"   if is_hw  and not is_sim else
               "mixed (sim and hw flags both active — run hw or sim to fix)" if is_sim else
               "neutral (no sim or hw flags set)")
    print(f"Mode  : {mode}")
    print(f"File  : {ini_path}")
    print("Flags :")
    for f in flags:
        tag = " ← sim" if f in SIM_FLAGS else " ← hw" if f in HW_FLAGS else ""
        print(f"  {f}{tag}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    mode = args[0] if args else ""
    if mode == "hardware":
        mode = "hw"
    if mode not in ("sim", "hw", "status"):
        print(__doc__)
        sys.exit(1)

    ini_path = find_ini()
    if not ini_path:
        sys.exit("ERROR: platformio.ini not found in current or parent directory.\n"
                 "Run this script from the project directory.")

    if mode == "status":
        show_status(ini_path)
    else:
        read_modify_write(ini_path, mode)


if __name__ == "__main__":
    main()
