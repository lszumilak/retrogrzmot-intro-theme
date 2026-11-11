#!/usr/bin/env python3
"""One dim amber logo at early boot; no userdata dependency or background DMA."""
import atexit
import fcntl
import time

def main():
    with open('/tmp/retrogrzmot-led-hardware.lock','a') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Early LED skipped: hardware already owned.',flush=True)
            return
        from rpi_ws281x import Color, PixelStrip, ws
        strip=PixelStrip(43,21,800000,10,False,255,0,ws.WS2811_STRIP_GRB)
        try:
            strip.begin()
            for index in range(43):
                strip.setPixelColor(index,Color(5,2,0) if index<5 else 0)
            strip.show()
            print(f'Early amber logo displayed at {time.monotonic():.3f}s after kernel start.',flush=True)
        finally:
            atexit.unregister(strip._cleanup)
            strip._cleanup()

if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        print('Early LED skipped: '+str(exc),flush=True)
        # Optional indicator must not block system startup.
