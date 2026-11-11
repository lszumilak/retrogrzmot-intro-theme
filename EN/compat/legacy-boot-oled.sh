#!/bin/bash
# RETROGRZMOT EARLY BOOT v1
case "$1" in
    start)
        (
            export PATH=/usr/sbin:/usr/bin:/sbin:/bin
            # Load interfaces before waiting for the device node.
            modprobe i2c-dev 2>/dev/null || true
            modprobe i2c-bcm2835 2>/dev/null || true
            python3 /boot/retrogrzmot-early/splash.py
        ) >> /tmp/retrogrzmot-early.log 2>&1 < /dev/null &
        ;;
esac
# Never block/fail the boot sequence if the display is disconnected.
exit 0
