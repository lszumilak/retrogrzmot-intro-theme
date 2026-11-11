#!/usr/bin/env python3
"""Observe EXIT/USB START only while the verified boot splash mpv is running."""
import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import struct
import time

running = True

def stop(*_):
    global running
    running = False

def verified_player(pid):
    try:
        args = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        return (Path(os.readlink(f'/proc/{pid}/exe')).name == 'mpv'
                and any(a.startswith(b'/userdata/splash/') or a == b'/usr/share/batocera/splash/splash.mp4' for a in args))
    except OSError:
        return False

def send_quit(pid, address):
    if not verified_player(pid):
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(0.5)
            conn.connect(address)
            peer_pid, _, _ = struct.unpack('3i', conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if peer_pid != pid:
                return False
            conn.sendall(b'{"command":["quit"]}\n')
        return True
    except OSError:
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pid-file', default='/var/run/user-splash.pid')
    ap.add_argument('--socket', default='/tmp/retrogrzmot-splash.sock')
    ap.add_argument('--usb-only', action='store_true', help='Do not request GPIO26')
    args = ap.parse_args()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    with open('/tmp/retrogrzmot-splash-skip.lock', 'a') as lock, contextlib.ExitStack() as stack:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        pid = 0
        deadline = time.monotonic() + 10
        while running and time.monotonic() < deadline:
            try:
                pid = int(Path(args.pid_file).read_text().strip())
            except (OSError, ValueError):
                pass
            if pid > 1 and verified_player(pid):
                break
            time.sleep(0.02)
        if not verified_player(pid):
            print('No verified splash player; watcher exits.', flush=True)
            return
        gpio = None
        try:
            if args.usb_only:
                raise ImportError('GPIO26 disabled by package selection')
            import gpiod
            from gpiod.line import Bias, Direction, Value
            gpio = stack.enter_context(gpiod.request_lines('/dev/gpiochip0', consumer='retrogrzmot_splash', config={
                26: gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, active_low=True)}))
            raw = stable = gpio.get_value(26) == Value.ACTIVE
            changed = time.monotonic()
            armed = False
            pressed = False
        except (ImportError, OSError) as exc:
            gpio = None
            if not args.usb_only:
                print('GPIO unavailable: ' + str(exc), flush=True)
        try:
            import evdev
            start_code = evdev.ecodes.BTN_START
        except ImportError:
            evdev = None
            print('evdev unavailable; USB START disabled.', flush=True)
        devices = {}
        next_scan = 0.0
        pending = None
        deadline = time.monotonic() + 120
        print(f'READY splash PID={pid}; GPIO26 EXIT and USB BTN_START; release to skip', flush=True)
        try:
            while running and verified_player(pid) and time.monotonic() < deadline:
                now = time.monotonic()
                if gpio is not None:
                    value = gpio.get_value(26) == Value.ACTIVE
                    if value != raw:
                        raw, changed = value, now
                    if now - changed >= 0.06:
                        if stable != raw:
                            stable = raw
                            if stable:
                                pressed, armed = armed, False
                            elif pressed:
                                pending, pressed = 'EXIT', False
                        if not stable:
                            armed = True
                if evdev is not None and now >= next_scan:
                    next_scan = now + 0.4
                    for path in evdev.list_devices():
                        if path in devices:
                            continue
                        device = None
                        try:
                            device = evdev.InputDevice(path)
                            caps = device.capabilities()
                            sys_device = Path('/sys/class/input') / Path(path).name / 'device'
                            physical = '/devices/virtual/' not in str(sys_device.resolve())
                            if (physical and device.name != 'batocera hotkeys'
                                    and device.info.bustype == 0x03
                                    and start_code in caps.get(evdev.ecodes.EV_KEY, [])):
                                # A held button at discovery must be released before it can skip.
                                devices[path] = [device, False, start_code not in device.active_keys()]
                                print('USB controller: ' + device.name, flush=True)
                                device = None
                        except OSError:
                            pass
                        finally:
                            if device is not None:
                                device.close()
                for path, item in list(devices.items()):
                    device, held, enabled = item
                    try:
                        try:
                            events = list(device.read())
                        except BlockingIOError:
                            events = []
                        for event in events:
                            if event.type == evdev.ecodes.EV_KEY and event.code == start_code:
                                if event.value == 1 and enabled:
                                    held = True
                                elif event.value == 0:
                                    if held:
                                        pending = 'USB START'
                                    held, enabled = False, True
                        devices[path] = [device, held, enabled]
                    except OSError:
                        device.close()
                        del devices[path]
                if pending and send_quit(pid, args.socket):
                    print('SKIPPED via ' + pending, flush=True)
                    return
                time.sleep(0.01)
        finally:
            for device, _, _ in devices.values():
                device.close()
            print('Watcher exits; GPIO26 released for the game EXIT service.', flush=True)

if __name__ == '__main__':
    main()
