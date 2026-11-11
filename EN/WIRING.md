# Połączenia / Wiring — Raspberry Pi 3B+

BCM identifies the GPIO signal; physical numbers identify positions on the 40-pin header. D26 on the tested FAN Adapter V2 means BCM26. Shut down and disconnect console and LED supplies before wiring. / Numery BCM oznaczają sygnały, fizyczne — miejsca na złączu. Podłączaj przy odłączonych zasilaczach.

| Funkcja / Function | BCM | Pin fizyczny / Physical | Połączenie / Connection |
| --- | --- | --- | --- |
| POWRÓT / RETURN | 26 | 37 | Normally-open momentary switch to a free GND; no voltage rail |
| RETURN GND | — | E.g. 34 | Free ground; the owner’s actual GND pin was not recorded |
| LED DATA | 21 | 40 | LED REV C J3 pin 2 |
| LED GND | — | 39 in the PCB guide | LED REV C J3 pin 1; grounds shared |
| OLED SDA | 2 | 3 | SSD1306 SDA |
| OLED SCL | 3 | 5 | SSD1306 SCL |
| OLED VCC | — | 1 | 3.3 V, not 5 V |
| OLED GND | — | 6 | Ground |
| SHIM control | 4 | 7 | SHIM physical pin 7 → D4 |
| SHIM button signal | 17 | 11 | SHIM physical pin 11 → D17 |
| SHIM 5 V | — | 2 | SHIM physical pin 2 → adapter 5 V |
| SHIM GND | — | E.g. 20 | SHIM physical pin 6 → adapter GND |
| POWER button | — | SHIM BTN pads | One contact to each BTN pad |

Wszystkie GND złącza Pi mają wspólną masę: fizyczne 6, 9, 14, 20, 25, 30, 34, 39. Jeśli jeden jest zajęty, wybierz inny wolny. / Pi header GND pins share ground; use another free one if needed.

WS2812B uses the RETROGRZMOT LED REV C buffer circuit and a separate supply. Positive supply rails remain separate. The package does not change wiring or automatically control the Pololu 2810 ON pin. The tested driver sends 43 positions, with five logo pixels and animated base positions 6–40. Higher brightness/full-load white is not certified by this package.

Zasilacz Pi podłącz do microUSB SHIM-a; przy tej konfiguracji gniazdo microUSB Pi pozostaje puste. Ustawienia SHIM włączaj tylko przy rzeczywistym podłączeniu tego modułu. / Power the Pi through the SHIM micro-USB input, leaving the Pi micro-USB input empty in that setup. Enable SHIM only when it is actually wired.

- [Official Raspberry Pi GPIO reference](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio)
- [RETROGRZMOT LED REV C guide](https://retrogrzmot.pages.dev/downloads/led-pcb-rev-c/opis.html)
- [RETURN wiring diagram](https://github.com/lszumilak/retrogrzmot-return-button/blob/main/wiring.svg)
- [OnOff SHIM guide](https://github.com/lszumilak/retrogrzmot-shim)
- [OLED guide](https://github.com/lszumilak/retrogrzmot-oled)
