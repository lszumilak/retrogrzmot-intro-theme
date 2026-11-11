# Validation / Weryfikacja

Target: Raspberry Pi 3B+ / Batocera 43.1. The release uses a selected-equipment installer; it does not download arbitrary current branch heads during installation.

## Prior device tests

- Aircraft intro PL/EN: all 384 frames decoded, final language labels and pixel skip notices inspected, audio copied unchanged from the approved short versions.
- GPIO26 RETURN: physical signal and repeated game exits confirmed by the owner.
- Intro skipping: owner rebooted and confirmed that RETURN skips the real startup movie and still exits games afterwards.
- Early amber logo: owner accepted the brightness and confirmed boot handover to existing lighting. It appears with OLED, at most about half a second earlier, rather than immediately on POWER.
- OLED, LED effects/settings panel and OnOff SHIM have separate project/device histories. They are included at the public commits recorded in package.json.
- START on a USB controller is implemented but has not been physically tested in this session; the owner’s controller was connected through Bluetooth. Bluetooth becomes available after the movie in the tested boot sequence.

## Bundle installation tests

The distribution includes `tests/test_installer.py`. It creates temporary filesystem roots and applies the actual installation plans and transactions there. It does not mount or modify the real boot partition, start services, reboot, or drive GPIO/LEDs.

Checks cover package integrity, optional modules, language preservation, existing LED settings, repeated installation, legacy/custom boot hooks, USB-only skip, ambiguous settings, failures at several write stages, failed overlay-save rollback, exact uninstallation, preservation of unrelated later settings and reverse-order restoration of updates. SHIM/OLED-specific tests run only in Complete.

Run in a test/development environment:

```sh
python3 tests/test_installer.py
```

This validates installer behavior in isolated roots. It is not a complete physical installation/reinstallation test of every bundle/hardware combination. Final release evidence and counts are provided alongside the ZIPs in `validation-report.json`.

The root installer’s `--check` additionally checks the actual device model/version and required tools, libraries, GPIO ownership and current file layouts. It does not initialize the strip or display. After installing, use the manual checklist in README and restart from Batocera’s menu.
