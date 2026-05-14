# Available Components

## Primary Microcontrollers

### Arduino-Compatible Boards

#### ELEGOO Mega 2560 R3
- ATmega2560
- 5V logic
- large GPIO count
- ideal for sensor projects and learning electronics
- compatible with Arduino IDE and PlatformIO

#### ESP32-S3 DevKitC-1 (N16R8)
- ESP32-S3-WROOM-1
- WiFi + Bluetooth 5
- dual-core MCU
- 3.3V logic
- significantly more powerful than Mega2560
- supports USB serial
- suitable for IoT, networking, displays, async systems

IMPORTANT:
- ESP32-S3 uses 3.3V logic
- avoid connecting 5V outputs directly to GPIO pins

---

# Breadboarding & Prototyping

- solderless breadboard
- jumper wires
- Dupont wires
- USB cables (various)

## USB Cables & Adapters

### USB-B to USB-A Cable (Printer Cable)
- Male USB-B (Type B square plug) → Male USB-A
- Standard 1–2 m length
- Used to connect Yamaha P-125 USB-B port to host/adapter

### Mepsies USB-C to USB 3.0 OTG Adapter (3 pack, Grey)
- USB-C male → USB-A female (OTG)
- USB 3.0 / backwards-compatible with USB 2.0
- Physical: 30.5 × 16 × 7.6 mm aluminium body
- Allows USB-C devices (e.g. ESP32-S3 native USB port) to HOST USB-A peripherals
- Product: Mepsies USB C to USB 3.0 OTG Adapter — Amazon
- IMPORTANT: this adapter makes the USB-C port a HOST (not a device)

---

## Storage

### Micro SD Card (16 GB)
- 16 GB capacity, standard microSD format
- Formatted FAT32 (required by Arduino SD library)
- Used with Micro SD Card Reader Module via SPI

### Micro SD Card Mini TF Reader Module
- Supplier: Switch Electronics (switchelectronics.co.uk)
- Interface: SPI (4-wire: MOSI, MISO, SCK, CS) + power (VCC, GND)
- Operating voltage: 3.3 V (compatible with ESP32-S3 directly, no level-shifting needed)
- 6-pin single-row header (2.54 mm pitch)
- Module PCB with built-in micro SD slot — connect via 6 jumper wires
- Compatible with Arduino SD library

---

# LEDs

- red LEDs
- green LEDs
- blue LEDs
- yellow LEDs
- RGB LED

Available for:
- status indicators
- PWM dimming
- animations
- state-machine debugging

---

# Passive Components

## Resistors
Available resistor values include:
- 10R
- 100R
- 220R
- 330R
- 1K
- 2K
- 5.1K
- 10K
- 100K
- 1M

## Other
- potentiometer
- photoresistor (LDR)

---

# Input Components

- push buttons
- tilt switch

Possible uses:
- user interfaces
- interrupts
- menu systems
- event triggers

---

# Audio Components

- active buzzer

Possible uses:
- alarms
- notifications
- simple sound output

---

# Display Components

## LCD1602
- character LCD display
- suitable for menus and status displays

---

# Sensors

## GY-521 (MPU6050)
- accelerometer
- gyroscope
- I2C interface

## Photoresistor
- ambient light sensing

## Tilt Switch
- orientation / movement detection

---

# Motor & Driver Components

## DC Motor

## Servo Motor

## Stepper Motor

## L293D Motor Driver
- H-bridge motor control

Possible uses:
- robotics
- motion systems
- pan/tilt systems

---

# Digital Logic Components

## 74HC595 Shift Register
Useful for:
- driving many LEDs
- expanding outputs
- learning SPI-like communication

---

# Power Constraints

## Arduino Mega 2560
- 5V logic system

## ESP32-S3
- 3.3V logic system
- GPIO pins are NOT 5V tolerant

IMPORTANT:
- when mixing ESP32-S3 with 5V modules, verify voltage compatibility

---

# Software Environment

Installed Tools:
- VS Code
- PlatformIO
- Wokwi

Preferred workflow:
- PlatformIO projects
- Wokwi simulation
- serial-debug driven development
- iterative compile/test/debug loops

---

# Preferred AI Workflow

The AI assistant may:
- generate PlatformIO firmware
- generate Wokwi diagram.json files
- simulate projects
- inspect serial logs
- iterate on implementations
- propose alternative architectures
- produce wiring instructions
- generate README documentation

The AI assistant should:
- prefer components already available
- avoid requiring additional hardware unless necessary
- prefer simulatable designs where possible
- use non-blocking Arduino code patterns
- avoid delay() when practical

---

# Preferred Project Types

Interested areas:
- IoT devices
- sensor systems
- automation
- displays and dashboards
- robotics
- LED animations
- WiFi-connected systems
- Bluetooth systems
- home monitoring
- embedded software architecture

---

# Simulation Notes

Wokwi simulation is preferred when possible.

Well-supported in simulation:
- LEDs
- buttons
- displays
- serial output
- I2C devices
- many sensors
- ESP32 networking logic

Less reliable in simulation:
- analog edge cases
- power behavior
- RF behavior
- noisy motor systems
- precise timing issues

---

# Design Preferences

Preferred:
- modular code
- reusable components
- clean architecture
- serial logging
- structured JSON debug output
- finite-state-machine designs
- async/non-blocking patterns

Avoid:
- blocking delays
- giant loop() functions
- hardcoded pin numbers scattered throughout code
- unnecessary libraries