# RETROGRZMOT — Batocera bundles, step by step

Release 1.0.0 · 11 November 2026 · **Raspberry Pi 3 Model B+ / Batocera 43.1** · [Polski](README.pl.md)

`package.json` identifies this bundle and its language. The installer preserves Batocera’s interface language. PL/EN selects the movie and the initial language of a newly installed OLED; an existing OLED language selection is retained. The LED panel follows Batocera’s language, using Polish or English for other languages.

## Choose one bundle

| Bundle | Contents |
| --- | --- |
| Intro & Theme | Public 16-second aircraft intro, black/purple Carbon styling, logo and lightning, loading screen, optional skip controls and dim early LED logo |
| Complete | All of the above plus optional OLED, RETURN to exit games, LED service/settings panel, and OnOff SHIM configuration |

Install **one** bundle. Complete includes the smaller bundle. Existing LED preferences and unrelated services are retained. Selecting fewer modules does not uninstall existing add-ons.

The public movie contains aircraft only. PL uses “System do gier retro” and “Wciśnij POWRÓT żeby pominąć”; EN uses “Retro games system” and “Press RETURN to skip”. The notice shares the movie’s pixel font, glow and CRT/VHS filters, with POWRÓT/RETURN in bold.

## 1. Check your hardware

Start with working Batocera 43.1 on a Pi 3B+, a display, controller, and Windows computer on the same network. The **Carbon** theme must already be present. The bundle includes its own Carbon overrides rather than a copy of the author’s operating system/card.

Select only hardware you have wired. See [WIRING.md](WIRING.md):

- RETURN: normally-open momentary button between BCM GPIO26 (D26, physical pin 37) and a free GND.
- LEDs: RETROGRZMOT WS2812B circuit, separate power supply, shared ground, GPIO21 (physical pin 40), and HDMI audio. The driver sends 43 positions: five logo pixels, with animated base effects using positions 6–40.
- OLED: 128×64 SSD1306, I²C address 0x3C, 3.3 V supply.
- POWER: wired Pimoroni OnOff SHIM PIM269 on GPIO4/17, button on its BTN pads, and Pi power through the SHIM as described in its guide.

Do not move correctly installed wires. Shut down and unplug both power supplies before changing wiring. D26 means BCM26, **not physical pin 26**. A different POWER button/controller is not an OnOff SHIM.

## 2. Download and extract

Choose Intro & Theme or Complete, ending in `-pl.zip` or `-en.zip`. In Windows, right-click the ZIP and choose **Extract All**. The extracted folder must contain `install.sh`, `install.py`, `package.json`, `FILES.json`, and `payload`.

Copy the entire folder, not just the installer.

## 3. Copy to Batocera and connect

Find the console IP in Batocera’s **Network Settings**. In File Explorer enter `\\CONSOLE_IP\share`, replacing `CONSOLE_IP`. Open `system` and copy the extracted folder there.

If the network share is unavailable, open PowerShell in the folder containing the extracted bundle. Example for Complete EN; replace the console address:

```powershell
scp -r .\retrogrzmot-complete-v1.0.0-en root@CONSOLE_IP:/userdata/system/
ssh root@CONSOLE_IP
```

The smaller bundle is `retrogrzmot-intro-theme-v1.0.0-en`; Polish bundles end in `-pl`. Verify the console address before accepting its key on first connection. Enter your Batocera password; the terminal displays no password characters. [Batocera SSH help](https://wiki.batocera.org/access_the_batocera_via_ssh).

## 4. Choose modules and check first

Close any game and the LED settings panel, leaving Batocera in its menu. The following commands run **on the console through SSH**.

Complete:

```sh
bash /userdata/system/retrogrzmot-complete-v1.0.0-en/install.sh --check
```

Intro & Theme:

```sh
bash /userdata/system/retrogrzmot-intro-theme-v1.0.0-en/install.sh --check
```

Answer the hardware questions. `y` means yes; Enter means no. Theme and movie are the shared base. Hardware add-ons require your explicit selection.

- **GPIO26 RETURN skip:** select for the physical button. Press and release to skip; USB START is also supported.
- **USB START only:** for a wired controller or compatible USB receiver without a GPIO button. GPIO26 is not requested. The device must report standard BTN_START. Bluetooth starts after the movie in the tested boot sequence.
- **OLED, LEDs, SHIM:** select only your actual wired hardware.
- **Dim early logo:** lights five logo pixels in faint amber and requires powered LED hardware. On the tested console it appears with the OLED, at most about half a second earlier, rather than immediately when POWER is pressed. The full LED service later takes over. With only the smaller bundle and no full LED service, the logo remains dimly lit.
- **RETURN exits games:** in Complete this also enables GPIO26 intro skipping.

`CHECK OK` means no files were changed. If `STOP` appears, resolve the reported missing library, GPIO conflict, other power controller, or unfamiliar startup script first.

## 5. Install

Run the appropriate command again without `--check`, selecting the same hardware:

```sh
bash /userdata/system/retrogrzmot-complete-v1.0.0-en/install.sh
```

For Intro & Theme use this instead:

```sh
bash /userdata/system/retrogrzmot-intro-theme-v1.0.0-en/install.sh
```

The installer verifies package integrity, prepares all edits, creates a unique backup, then writes files. It preserves interface language, LED preferences and unrelated services. It enables movie sound while keeping system volume. Other startup movies are backed up and removed from the movie-selection folder so Batocera plays the intended movie.

Keep the full `Backup:` path and `Restore:` command. A write failure triggers an attempt to restore the previous files. If saving the system overlay itself fails, retain the message and backup and avoid abruptly cutting power.

The installer **does not reboot, restart services, or run lighting effects during installation**. After `Installed`, restart normally from Batocera’s menu. Repeating the same installation should report that no changes are needed.

## 6. Test after restarting

1. The aircraft movie appears in the chosen language with its skip notice.
2. RETURN skips the movie; in the game list it should not select a game. Test START with a USB controller.
3. Carbon has the black background, purple accents, logo and lightning.
4. With OLED selected, check system selection, game launch and return.
5. With game RETURN selected, launch a game, press/release RETURN and verify return to the current system’s game list. Repeat.
6. With LEDs selected, open **Ports → Sterowanie podświetleniem RETROGRZMOTA**. The panel follows the interface language. Check both zones. The default 30% slider corresponds to roughly 3% strip level; the 100% slider is capped at roughly 10%. Existing preferences are retained.
7. With SHIM selected, separately test normal shutdown and power-on. Do not test power cuts during installation or writes.

## Restore and update

Backups live in `/userdata/system/retrogrzmot-bundle-backups/`. Use the exact `Restore:` command printed by the installer. Its form is:

```sh
python3 /userdata/system/retrogrzmot-bundle-backups/IDENTIFIER/restore.py --uninstall /userdata/system/retrogrzmot-bundle-backups/IDENTIFIER
```

Replace both `IDENTIFIER` values with the actual backup folder. Restore installations **newest first**. This restores previous movies, module files and settings. Unrelated later settings in `batocera.conf` and interface-language choices are retained. If a managed theme/startup file was edited manually, restoration stops for review instead of overwriting that edit. Backups remain on the card.

Restart normally after restoring. Empty leftover directories do not enable any add-on.

## Validation

[TESTING.md](TESTING.md) distinguishes isolated installation/rollback checks from prior hardware tests. Publication alone does not mean every possible hardware selection was tested physically.

Useful logs after boot: `/tmp/retrogrzmot-splash-skip.log`, `/tmp/retrogrzmot-early-led.log`, `/tmp/retrogrzmot-early.log`, `/tmp/retrogrzmot-exit.log`, `/tmp/retrogrzmot-oled.log`. Files in `/tmp` clear at reboot.

[Credits and components](ATTRIBUTION.md) · [Wiring](WIRING.md) · [Changelog](CHANGELOG.md)
