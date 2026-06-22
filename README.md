# DLP2000 EVM + Raspberry Pi 5 Projector Controller

Drive a **DLPDLCR2000EVM** (DLP2000 LaunchPad) projector from a Raspberry Pi 5 using the 40-pin DPI parallel video interface and software I2C for DLPC3430 control.

## Hardware Requirements

| Component | Details |
|---|---|
| Projector | DLPDLCR2000EVM (DLP2000 LaunchPad) |
| Host | Raspberry Pi 5 |
| Interface | RGB666 DPI (parallel video) via 40-pin header |
| Control | Software I2C — GPIO23 (SDA), GPIO24 (SCL) |
| USB (optional) | TI NIRscan Nano spectrometer (VID 0451 / PID 4200) |

See `dlp2000_correct_pinout.txt` for the full pin mapping between the DLP2000 EVM 40-pin header and Raspberry Pi GPIO.

## Software Dependencies

```bash
pip install -r requirements.txt
```

Requirements: `smbus2`, `Pillow`, `mss`, `numpy`, `opencv-python-headless`

Also required (system packages):

```bash
sudo apt install python3-pygame i2c-tools
```

## Setup

### 1. Install udev rule (USB NIR scanner)

```bash
sudo cp 99-nirscanner.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

### 2. Initialize DLP as a second screen

This loads the DPI and software I2C overlays at runtime — no `/boot/config.txt` changes needed:

```bash
sudo bash antigravity_start.sh
```

After this succeeds:
- DLP appears as `/dev/fb1`
- Positioned at `1920,0` (right of HDMI primary)
- DLPC3430 initialized via I2C

Run once per boot. Safe to re-run — skips steps already done.

## Scripts

### Display

| Script | What it does |
|---|---|
| `screen_mirror.py` | Mirror a region of the desktop to the DLP in real-time |
| `screen_mirror_bgr.py` | Same, with BGR channel swap |
| `screen_mirror_custom.py` | Mirror with custom crop/scale parameters |
| `display_image.py [path]` | Display a still image fullscreen on the projector |
| `show_white.py` | Solid white (full brightness test) |
| `show_red.py` | Solid red (R channel isolation) |
| `show_green.py` | Solid green (G channel isolation) |
| `show_blue.py` | Solid blue (B channel isolation) |
| `show_static.py` | Static noise pattern |
| `show_random.py` | Animated random noise |
| `show_color_custom.py` | Custom RGB color via args |
| `show_image_pygame.py [path]` | Display image via Pygame |
| `show_image_chromium.sh` | Display image via Chromium fullscreen |
| `show_pattern_window.py` | Render a pattern in a window |

### Patterns & I2C Control

| Script | What it does |
|---|---|
| `loop_patterns.py` | Loop through diagnostic + structural patterns |
| `change_pattern.py <index>` | Switch DLPC3430 to a specific internal test pattern |
| `dlp_controller.py` | DLPC3430 I2C library (import in your own scripts) |
| `poll_i2c.py` | Poll DLPC3430 status register continuously |
| `check_shorts.py` | Diagnose GPIO shorts / I2C bus faults |
| `test_active_pins.py` | Toggle GPIO pins to verify DPI wiring |
| `test_custom_descramble.py` | Verify RGB bit-order descrambling |

### Utilities

| Script | What it does |
|---|---|
| `antigravity_start.sh` | Runtime DLP init (DPI overlay + I2C overlay + xrandr) |
| `requirements.txt` | Python dependencies |
| `dlp2000_correct_pinout.txt` | Full GPIO ↔ DLP pin mapping reference |
| `dlp2000_pins.txt` | Condensed pin reference |

## Quick Start

```bash
# 1. Init hardware
sudo bash antigravity_start.sh

# 2. Test — solid white
python3 show_white.py

# 3. Mirror desktop
python3 screen_mirror.py

# 4. Display an image
python3 display_image.py /path/to/image.jpg

# 5. Loop test patterns
python3 loop_patterns.py
```

## Related

NIRscan Nano spectrometer driver and web app: [MicroscopeMaestro/NIRscanNano](https://github.com/MicroscopeMaestro/NIRscanNano)

## Troubleshooting

**`/dev/fb1` not found after `antigravity_start.sh`** — check DPI wiring (pixel clock and data lines). Verify `dtoverlay vc4-kms-dpi-generic` loaded with `dtoverlay -l`.

**I2C not found** — confirm GPIO23/24 are connected to `I2C2_SDA`/`I2C2_SCL` on the DLP EVM P2 header. Run `i2cdetect -l` to list buses and `i2cdetect -y <bus>` to scan for `0x1b`.

**Wrong colors** — check `dlp2000_correct_pinout.txt` for the RGB666 bit assignments. The `show_white.py` uses value `252` (not `255`) to match RGB666 6-bit alignment.
