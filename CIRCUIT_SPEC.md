# Circuit Specification

## Goal

Build an ambient light sensor that displays the current light level on an LCD screen.

## Functional Requirements

- Read ambient light level using a photoresistor (LDR)
- Display the light level as a percentage (0–100%) on an LCD1602 display
- Update the displayed value every 1 second
- Output structured JSON readings on the serial port for automated testing

## Hardware Constraints

- Target MCU: ESP32-S3 DevKitC-1 (N16R8)
- Display: LCD1602 (16×2 character LCD, 4-bit parallel mode)
- Sensor: Photoresistor / LDR via wokwi-photoresistor-sensor module in simulation
- All components drawn from COMPONENTS.md
