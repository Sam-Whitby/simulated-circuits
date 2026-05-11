# Wokwi Component Reference

Maps physical components from COMPONENTS.md to their Wokwi simulation equivalents.
Pin names here are the exact strings to use in diagram.json connections.

## MCU Boards

| Physical Board | Wokwi Part Type | Board File |
|---|---|---|
| ESP32-S3 DevKitC-1 | `board-esp32-s3-devkitc-1` | [board.json](https://raw.githubusercontent.com/wokwi/wokwi-boards/main/boards/esp32-s3-devkitc-1/board.json) |
| Arduino Mega 2560 | `board-arduino-mega` | [board.json](https://raw.githubusercontent.com/wokwi/wokwi-boards/main/boards/arduino-mega/board.json) |

### ESP32-S3 DevKitC-1 — Required Serial Monitor Wiring

Every diagram.json using this board **must** include these connections for wokwi-cli to capture serial output:

```json
["esp:TX", "$serialMonitor:RX", "", []],
["esp:RX", "$serialMonitor:TX", "", []]
```

Also required in platformio.ini:

```ini
build_flags = -DARDUINO_USB_CDC_ON_BOOT=0
```

Without these, the board uses native USB CDC (not captured by wokwi-cli serial log).

### ESP32-S3 DevKitC-1 Pin Naming

GPIO pins use numeric names only — NOT "GPIO4", just `"4"`.

| Label | diagram.json name |
|---|---|
| GPIO1–GPIO48 | `1` – `48` |
| 3.3V | `3V3.1`, `3V3.2` |
| GND | `GND.1`, `GND.2`, `GND.3`, `GND.4` |
| 5V | `5V` |
| EN / RST | `RST` |

---

## Sensors

| Physical Component | Wokwi Part Type | Pins | Notes |
|---|---|---|---|
| Photoresistor / LDR | `wokwi-photoresistor-sensor` | `VCC`, `GND`, `AO`, `DO` | Use AO for analog. Control: `lux` (0–100000). Do NOT use `wokwi-photoresistor` — pin names undocumented. |
| MPU6050 / GY-521 | `wokwi-mpu6050` | `VCC`, `GND`, `SCL`, `SDA`, `INT` | Controls: `accelX/Y/Z`, `gyroX/Y/Z`, `temperature` |
| DHT22 | `wokwi-dht22` | `VCC`, `SDA`, `GND` | Controls: `temperature`, `humidity` |

---

## Displays

| Physical Component | Wokwi Part Type | Pins | Notes |
|---|---|---|---|
| LCD1602 (parallel) | `wokwi-lcd1602` | `VSS`, `VDD`, `V0`, `RS`, `RW`, `E`, `D0`–`D7`, `A`, `K` | Use `attrs: {"pins":"full"}` to expose all 16 pins. V0 → potentiometer for contrast. |
| LCD1602 (I2C) | `wokwi-lcd1602` | `GND`, `VCC`, `SDA`, `SCL` | Use `attrs: {"pins":"i2c"}`. Simpler wiring. |

---

## Inputs

| Physical Component | Wokwi Part Type | Pins | Notes |
|---|---|---|---|
| Push button | `wokwi-pushbutton` | `1.l`, `1.r`, `2.l`, `2.r` | Control: `pressed` (0 or 1) |
| Potentiometer | `wokwi-potentiometer` | `GND`, `SIG`, `VCC` | Control: `value` (0–1023) |
| Tilt switch | `wokwi-tilt-switch` | `1`, `2` | Control: `tilt` (0 or 1) |

---

## Passives

| Physical Component | Wokwi Part Type | Pins | Notes |
|---|---|---|---|
| Resistor | `wokwi-resistor` | `1`, `2` | Set `attrs: {"value":"10000"}` for 10K |
| LED (single colour) | `wokwi-led` | `A`, `K` | Set `attrs: {"color":"red"}` etc. |
| RGB LED | `wokwi-rgb-led` | `R`, `G`, `B`, `COM` | |

---

## Audio

| Physical Component | Wokwi Part Type | Pins | Notes |
|---|---|---|---|
| Active buzzer | `wokwi-buzzer` | `1`, `2` | Drive pin 1 HIGH to sound |

---

## Motors & Drivers

| Physical Component | Wokwi Part Type | Pins | Notes |
|---|---|---|---|
| Servo motor | `wokwi-servo` | `V+`, `GND`, `PWM` | |
| DC motor | `wokwi-motor` | `A`, `B` | |

---

## Looking Up Unknown Parts

If a component isn't listed here, find its Wokwi part type and pins before writing diagram.json:

1. Search the Wokwi docs: `https://docs.wokwi.com/parts/wokwi-{component}`
2. Hover over pins in the Wokwi web editor to see exact pin names
3. Run `~/.wokwi/bin/wokwi-cli lint` after writing diagram.json — it will flag unknown part types
