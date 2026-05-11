# Assembly Instructions: Ambient Light Sensor with LCD Display

> **This document was generated from a validated breadboard.yaml layout.**
> Every hole reference has been checked by `breadboard_validator.py` to confirm
> it is unoccupied and physically accessible before these instructions were written.

Read through this document once before touching anything. Then work through each
step in order. Do not skip steps or work ahead.

---

## What You Are Building

An ambient light sensor that:
- Reads the brightness in the room using a photoresistor (a small disc-shaped component
  whose electrical resistance drops when light hits it)
- Displays the current level as a percentage on a character display (0% = dark, 100% = bright)
- Updates the reading once per second

---

## Parts List

Gather every item before you start.

| # | Component | Qty | Identifying features |
|---|-----------|-----|----------------------|
| 1 | ESP32-S3 DevKitC-1 (N16R8) | 1 | Black PCB, USB-C port, two rows of pins on the long sides |
| 2 | LCD1602 display — 16×2 characters, 16-pin single-row header | 1 | Green or blue PCB with a rectangular display window |
| 3 | Potentiometer, 10K ohm, breadboard-compatible | 1 | Small body with a rotatable shaft, three pins underneath |
| 4 | Photoresistor (LDR) | 1 | Small disc with a wavy line pattern, two flexible metal leads |
| 5 | Resistor, 10K ohm — bands: brown-black-orange-gold | 1 | Small cylinder with wire leads |
| 6 | Full-size solderless breadboard — 830 points | 1 | 63 rows, columns A–J, power rails top and bottom |
| 7 | Jumper wires, male-to-male, assorted colours | ≈ 20 | Red, black, blue, green, yellow, white, purple, orange |
| 8 | USB-C cable | 1 | To connect ESP32 to your computer |
| 9 | Computer with firmware already flashed onto the ESP32 | 1 | See WORKFLOW.md |

> ⚠️ **3.3 V logic only.** The ESP32-S3 is damaged by 5 V on its GPIO pins.
> Every connection in this circuit operates at 3.3 V.

---

## Understanding the Breadboard

### Hole coordinates

Every hole is named **ColumnRow** — the column letter followed by the row number.

- Columns **A–E** are on the LEFT side of the centre gap.
- Columns **F–J** are on the RIGHT side of the centre gap.
- Rows are numbered **1** (top) to **63** (bottom).

Examples: **B1** = column B row 1, **D41** = column D row 41, **J4** = column J row 4.

### Which holes are connected?

All five holes in the same row-half share one electrical node:
- **A5, B5, C5, D5, E5** are all connected to each other.
- **F5, G5, H5, I5, J5** are all connected to each other.
- The two halves of row 5 are **not** connected unless you run a wire between them.

### Power rails

The (+) and (−) strips at the top edge run the full width of the board:
- **(+) rail = 3.3 V**
- **(−) rail = Ground (0 V)**

### The one-hole-one-pin rule

**A breadboard hole accepts exactly one pin or wire at a time.** If a component lead is
already in a hole, a jumper wire must go into a *different* hole in the same row-half —
which is electrically identical but physically free.

---

## ESP32-S3 Pin Reference

Place the ESP32 with the USB-C connector at the top. The left header occupies
**column A** and the right header occupies **column I**, rows 1–22.

> ⚠️ **GPIO numbers do NOT equal row numbers.** GPIO 8 is at row 12 (A12), and
> GPIO 9 is at row 15 (A15). Always use the table below — never guess from the number.

### Left header — column A, rows 1–22

| Hole | Signal | Role in this circuit |
|------|--------|----------------------|
| A1  | 3.3 V | ✅ Power (wire uses **B1**) |
| A2  | 3.3 V | — |
| A3  | RST | — |
| **A4**  | **GPIO 4** | ✅ → LCD RS (pin 4) — wire uses **B4** |
| **A5**  | **GPIO 5** | ✅ → LCD Enable (pin 6) — wire uses **B5** |
| **A6**  | **GPIO 6** | ✅ → LCD D4 (pin 11) — wire uses **B6** |
| **A7**  | **GPIO 7** | ✅ → LCD D5 (pin 12) — wire uses **B7** |
| A8  | GPIO 15 | — |
| A9  | GPIO 16 | — |
| A10 | GPIO 17 | — |
| A11 | GPIO 18 | — |
| **A12** | **GPIO 8** | ✅ → LCD D6 (pin 13) — wire uses **B12** — row 12, not row 8 |
| A13 | GPIO 3 | — |
| A14 | GPIO 46 | — |
| **A15** | **GPIO 9** | ✅ → LCD D7 (pin 14) — wire uses **B15** — row 15, not row 9 |
| A16 | GPIO 10 | — |
| A17 | GPIO 11 | — |
| A18 | GPIO 12 | — |
| A19 | GPIO 13 | — |
| A20 | GPIO 14 | — |
| A21 | 5 V | — |
| A22 | GND | ✅ Power (wire uses **B22**) |

### Right header — column I, rows 1–22

| Hole | Signal | Role in this circuit |
|------|--------|----------------------|
| **I1**  | GND | ✅ Power (wire uses **J1**) |
| I2  | TX | — |
| I3  | RX | — |
| **I4**  | **GPIO 1** | ✅ → LDR junction (ADC) — wire uses **J4** |
| I5  | GPIO 2 | — |
| I6–I22 | (other GPIO / GND) | — |

---

## Breadboard Layout Overview

```
Top power rail:  (+) = 3.3 V     (−) = GND
─────────────────────────────────────────────────────────────────
Rows  1–22   ESP32-S3 DevKitC-1
             Left header  → column A, rows 1–22
             Right header → column I, rows 1–22
─────────────────────────────────────────────────────────────────
Rows  1–26   ← ESP32 BOARD BODY (PCB overhangs this zone)
             Nothing else may be placed in rows 1–26
─────────────────────────────────────────────────────────────────
Rows 28–29   LDR photoresistor        col H  (H28 = 3V3, H29 = junction)
Rows 29–31   10K resistor             col G  (G29 = junction, G31 = GND)
─────────────────────────────────────────────────────────────────
Rows 33–35   Potentiometer            col C  (C33 = GND, C34 = wiper, C35 = VCC)
─────────────────────────────────────────────────────────────────
Rows 38–53   LCD1602 display          col E  (E38 = pin 1, E53 = pin 16)
─────────────────────────────────────────────────────────────────
```

---

## Step-by-Step Assembly

Do not connect the USB-C cable until **Step F2**.

---

### Part A — Place the ESP32 Board

*Goal: Seat the microcontroller so all 44 header pins are accessible in the breadboard grid.*

**Step A1.** Orient the breadboard with row 1 at the top and the power rails along the
top and bottom edges.

**Step A2.** Pick up the ESP32 board. Rotate it so the USB-C connector faces upward
(away from the breadboard body).

**Step A3.** Align the left-side pins over **column A, row 1** and the right-side pins
over **column I, row 1**. Press the board down evenly until all pins click into place.
The board body will bridge the centre gap.

> **Check:** Left top pin = **A1**, left bottom = **A22** (count 22 pins).
> Right top = **I1**, right bottom = **I22** (22 pins). If the count is off, lift and reseat.

> **Note on the board body:** The ESP32 PCB extends approximately 3–4 rows below pin A22/I22.
> This means rows 23–26 are physically underneath the board. Those holes are inaccessible
> — the remaining components are placed below row 27.

---

### Part B — Set Up the Power Rails

*Goal: Establish a 3.3 V bus and a Ground bus that all components will connect to.*

> Why not wire directly to the ESP32 pins? The power rail lets multiple components share
> the same supply without cramming wires into the same row as the ESP32.

> **Remember the one-hole-one-pin rule:** pins A1, A22, and I1 are already occupied by
> the ESP32. The wires in this section use the adjacent holes B1, B22, and J1 — same
> electrical node, free hole.

**Step B1.** Take a **red** jumper wire. Insert one end into **B1** (same row as A1 =
ESP32 3.3 V) and the other end into the **(+)** row of the top power rail.

**Step B2.** Take a **black** jumper wire. Insert one end into **B22** (same row as A22 =
ESP32 GND, left header) and the other end into the **(−)** rail.

**Step B3.** Take a second **black** jumper wire. Insert one end into **J1** (same row as
I1 = ESP32 GND, right header) and the other end into the **(−)** rail.

> After these three steps, the (+) rail is 3.3 V and the (−) rail is Ground.

---

### Part C — Light Sensor (LDR Voltage Divider)

*Goal: Build a circuit whose output voltage rises when bright and falls when dark.
The ESP32 reads this voltage on GPIO 1 (hole I4) and maps it to 0–100%.*

A photoresistor (LDR) and a fixed 10K resistor form a voltage divider:

```
  3.3 V ──[ LDR ]──┬──[ 10K resistor ]── GND
                   │
                 GPIO 1  (reads voltage here)
```

When bright, the LDR's resistance falls, pulling the junction voltage toward 3.3 V →
higher ADC reading → higher percentage. When dark, the LDR's resistance rises →
junction voltage falls → lower percentage.

The LDR occupies column H (rows 28–29) and the resistor occupies column G (rows 29–31).
They share the **junction node** at row 29: H29 and G29 are in the same row-half (right
half), so they are electrically connected even though they are in different holes.

**Step C1.** Take the **LDR**. Insert one lead into **H28** and the other into **H29**.
The LDR has no polarity — either lead can go into either hole.

**Step C2.** Take the **10K resistor** (brown-black-orange-gold). Insert one lead into
**G29** and the other into **G31**. No polarity.

> **Check:** H29 and G29 are both occupied (one by the LDR, one by the resistor).
> H29 and G29 are in the same row-half (both are in F–J), so they are electrically
> connected — this is the junction node. Row 30 is deliberately empty.

**Step C3.** Take a **red** wire. Insert one end into **F28** (same row-half as H28,
the 3.3 V end of the LDR) and the other end into the **(+)** rail.

**Step C4.** Take a **black** wire. Insert one end into **F31** (same row-half as G31,
the GND end of the resistor) and the other end into the **(−)** rail.

**Step C5.** Take a **yellow** wire. Insert one end into **F29** (same row-half as H29
and G29 — the junction node) and the other end into **J4** (same row-half as I4 =
ESP32 GPIO 1 — I4 is occupied, J4 is the free adjacent hole).

> **How it works:** The yellow wire carries the junction voltage to GPIO 1. Covering the
> LDR raises its resistance → junction falls → lower reading → lower percentage. This is
> the physically correct behaviour. If the percentage goes the wrong way, swap the LDR
> leads: remove it and swap H28 ↔ H29.

---

### Part D — Potentiometer (LCD Contrast Adjustment)

*Goal: Wire a knob so you can adjust display contrast. Without this, characters may be
invisible even when the display is powered.*

The potentiometer has three pins. The outer two connect to GND and 3.3 V. The centre
pin (wiper) outputs a variable voltage that controls the LCD's character darkness.

**Step D1.** Take the **potentiometer**. Insert its three pins into **C33** (GND end),
**C34** (wiper/centre), and **C35** (VCC end). The body sits above the breadboard.

> If your potentiometer has a rotary shaft, the centre pin is the wiper.

**Step D2.** Take a **black** wire. Insert one end into **B33** (same row as C33, the
GND end) and the other into the **(−)** rail.

**Step D3.** Take a **red** wire. Insert one end into **B35** (same row as C35, the VCC
end) and the other into the **(+)** rail.

**Step D4.** Take a **green** wire. Insert one end into **B34** (same row as C34 — the
wiper; C34 is occupied so use the free adjacent hole B34) and the other end into **D40**
(same row as E40, which will be the LCD contrast pin once the display is inserted).

---

### Part E — LCD1602 Display

*Goal: Seat the display and wire all 16 pins.*

The LCD uses 4-bit mode: pins 7–10 (D0–D3) are unused and left empty. Pins 11–14
(D4–D7) carry data. Pins 1–6 handle power and control. Pins 15–16 control the backlight.

**Step E1.** Pick up the LCD1602. Identify the 16-pin header along one long edge.

**Step E2.** Orient the display with pin 1 at the top, screen facing you. Align pin 1
over **E38** and pin 16 over **E53**. Press down until all 16 pins are seated. The
display body extends to the left.

> **Check:** Count from E38 to E53 — exactly 16 holes. Pin 1 is labelled VSS (GND),
> pin 16 is labelled K (backlight −). Verify pin 1 is at E38.

LCD pin assignments once seated:

| LCD pin | Name | Hole | Connection |
|---------|------|------|------------|
| 1 | VSS (GND) | E38 | (−) rail |
| 2 | VDD (3.3V) | E39 | (+) rail |
| 3 | V0 (contrast) | E40 | Potentiometer wiper — wired in Step D4 |
| 4 | RS | E41 | GPIO 4 |
| 5 | RW | E42 | (−) rail (write-only) |
| 6 | E (Enable) | E43 | GPIO 5 |
| 7–10 | D0–D3 | E44–E47 | **Leave empty** (4-bit mode) |
| 11 | D4 | E48 | GPIO 6 |
| 12 | D5 | E49 | GPIO 7 |
| 13 | D6 | E50 | GPIO 8 |
| 14 | D7 | E51 | GPIO 9 |
| 15 | A (backlight +) | E52 | (+) rail |
| 16 | K (backlight −) | E53 | (−) rail |

Now run the wires. All LCD pins are in column E; the wires all use column D (same row,
free hole).

**Step E3.** LCD GND: **black** wire, **D38** → **(−)** rail.

**Step E4.** LCD 3.3 V: **red** wire, **D39** → **(+)** rail.

*(Contrast — E40 — already connected by Step D4.)*

**Step E5.** LCD RW to GND: **black** wire, **D42** → **(−)** rail. This locks the
display in write-only mode.

**Step E6.** Backlight positive: **red** wire, **D52** → **(+)** rail.

**Step E7.** Backlight negative: **black** wire, **D53** → **(−)** rail.

> **Backlight note:** The backlight LED is connected directly to 3.3 V. Most 3.3 V LCD
> backlights have a forward voltage close to 3.3 V, so current is self-limiting. For a
> permanent build, place a 33 Ω resistor in series with D52.

**Step E8.** GPIO 4 → LCD RS (data/command):
**blue** wire, **B4** → **D41**.

**Step E9.** GPIO 5 → LCD Enable:
**purple** wire, **B5** → **D43**.

**Step E10.** GPIO 6 → LCD D4:
**orange** wire, **B6** → **D48**.

**Step E11.** GPIO 7 → LCD D5:
**yellow** wire, **B7** → **D49**.

**Step E12.** GPIO 8 → LCD D6:
**green** wire, **B12** → **D50**.

> ⚠️ **GPIO 8 is at row 12 (A12), not row 8.** Use B12 for this wire, not B8.

**Step E13.** GPIO 9 → LCD D7:
**white** wire, **B15** → **D51**.

> ⚠️ **GPIO 9 is at row 15 (A15), not row 9.** Use B15, not B9.

---

### Part F — Final Check and Power-On

*Goal: Verify every connection before applying power, then confirm the circuit works.*

**Step F1.** Before connecting the USB cable, tick off every wire in the table below.
Count as you go — you should have exactly 20 wires.

| # | From | To | Colour | Purpose |
|---|------|----|--------|---------|
| 1 | B1 | (+) rail | Red | ESP32 3.3 V → power bus |
| 2 | B22 | (−) rail | Black | ESP32 GND (left) → ground bus |
| 3 | J1 | (−) rail | Black | ESP32 GND (right) → ground bus |
| 4 | (+) rail | F28 | Red | 3.3 V → top of LDR |
| 5 | F31 | (−) rail | Black | Bottom of 10K resistor → GND |
| 6 | F29 | J4 | Yellow | LDR junction → GPIO 1 (ADC) |
| 7 | B33 | (−) rail | Black | Potentiometer GND end |
| 8 | B35 | (+) rail | Red | Potentiometer VCC end |
| 9 | B34 | D40 | Green | Potentiometer wiper → LCD contrast |
| 10 | D38 | (−) rail | Black | LCD VSS → GND |
| 11 | D39 | (+) rail | Red | LCD VDD → 3.3 V |
| 12 | D42 | (−) rail | Black | LCD RW → GND (write-only) |
| 13 | D52 | (+) rail | Red | LCD backlight + |
| 14 | D53 | (−) rail | Black | LCD backlight − |
| 15 | B4 | D41 | Blue | GPIO 4 → LCD RS |
| 16 | B5 | D43 | Purple | GPIO 5 → LCD Enable |
| 17 | B6 | D48 | Orange | GPIO 6 → LCD D4 |
| 18 | B7 | D49 | Yellow | GPIO 7 → LCD D5 |
| 19 | B12 | D50 | Green | GPIO 8 → LCD D6 |
| 20 | B15 | D51 | White | GPIO 9 → LCD D7 |

Also confirm:
- [ ] LDR leads in **H28** and **H29**
- [ ] 10K resistor leads in **G29** and **G31** (row 30 is empty)
- [ ] Potentiometer pins in **C33**, **C34**, **C35**
- [ ] LCD 16-pin header spans **E38** (pin 1) through **E53** (pin 16)
- [ ] Holes **E44–E47** (LCD D0–D3) are empty

**Step F2.** Connect the USB-C cable to the ESP32. Connect the other end to your computer.

**Step F3.** The backlight should illuminate within 3 seconds. You will see:

```
Light Sensor
Level: XX%
```

The percentage updates once per second.

**Step F4.** If the backlight is on but the display is blank or shows solid blocks, slowly
turn the potentiometer knob through its full range. Stop when you can read the text clearly.

**Step F5.** Test the sensor: cover the LDR completely with your hand. The percentage should
fall toward 0%. Uncover it and shine a torch directly at the disc — the percentage should
rise toward 100%.

---

## Troubleshooting

| Symptom | Most likely cause | Fix |
|---------|-------------------|-----|
| No backlight, display completely dark | Power wires missing | Recheck Steps B1–B3, E6, E7 |
| Backlight on, display blank or solid blocks | Contrast not adjusted | Turn potentiometer through full range; check Step D4 (B34 → D40) |
| Percentage stuck at 0% and does not change | LDR circuit not connected | Recheck C1–C5; confirm H29 and G29 both have component leads; confirm F29 → J4 |
| Percentage always at 100% | GND connection of divider missing | Recheck Step C4 (F31 → (−) rail) |
| Percentage falls when you shine light (inverted) | LDR leads swapped | Remove LDR; swap which lead goes into H28 and H29 |
| Text appears but is garbled or missing characters | Data wire wrong | Recheck E8–E13 against the table; confirm GPIO 8 uses B12 (not B8) and GPIO 9 uses B15 (not B9) |
| Backlight on, first row of blocks, second row blank | RS or Enable wiring wrong | Recheck E8 (B4 → D41) and E9 (B5 → D43) |
