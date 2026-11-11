#!/bin/bash
# Independent optional jobs; /userdata is not available at this boot stage.
case "$1" in
start)
    if [ -f /boot/retrogrzmot-early/enable-led ]; then
        (timeout 3 python3 /boot/retrogrzmot-early/early_led.py) >>/tmp/retrogrzmot-early-led.log 2>&1 </dev/null &
    fi
    if [ -f /boot/retrogrzmot-early/enable-oled ]; then
        (
            modprobe i2c-dev 2>/dev/null || true
            modprobe i2c-bcm2835 2>/dev/null || true
            timeout 10 python3 /boot/retrogrzmot-early/splash.py
        ) >>/tmp/retrogrzmot-early.log 2>&1 </dev/null &
    fi
    ;;
esac
exit 0
