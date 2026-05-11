# Dependencies

## Development Tools

| Tool | Version | Purpose | Install |
|---|---|---|---|
| VS Code | Latest | IDE | https://code.visualstudio.com |
| PlatformIO IDE extension | Latest | Build system | VS Code marketplace |
| Wokwi VS Code extension | Latest | In-IDE simulation | VS Code marketplace |
| wokwi-cli | 0.26.1+ | Headless simulation + CI | `curl -L https://wokwi.com/ci/install.sh \| sh` |
| Node.js | 18+ | Required by wokwi-cli | https://nodejs.org |

## PlatformIO Platform & Framework

| Package | Version | Notes |
|---|---|---|
| platform: espressif32 | 7.0.0+ | ESP32 PlatformIO platform |
| framework: arduino | — | Arduino framework for ESP32 |
| toolchain-xtensa-esp32s3 | 8.4.0+ | Compiler, installed automatically |

## Firmware Libraries

Declared in `platformio.ini`, installed automatically by PlatformIO:

| Library | Version | Purpose |
|---|---|---|
| arduino-libraries/LiquidCrystal | ^1.0.7 | LCD1602 4-bit parallel driver |

## Services & Authentication

| Service | Required | Notes |
|---|---|---|
| Wokwi account | Yes | Free tier: 50 min simulation/month |
| Wokwi CI token | Yes (for CLI) | Generate at https://wokwi.com/dashboard/ci |
| GitHub account | Yes (for this repo) | — |

## Environment Variables

```bash
# Required for wokwi-cli simulation runs
export WOKWI_CLI_TOKEN=<token-from-wokwi-dashboard>
```

Add to `~/.zshrc` or `~/.bashrc` for persistence.

## Build Flags (platformio.ini)

```ini
build_flags = -DARDUINO_USB_CDC_ON_BOOT=0
```

This routes `Serial` through hardware UART0 (GPIO43/44) rather than native USB CDC,
which is required for `wokwi-cli` to capture serial output.
