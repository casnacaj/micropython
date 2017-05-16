import uos
import network
from flashbdev import bdev

def wifi():
    import ubinascii
    ap_if = network.WLAN(network.AP_IF)
    essid = b"MicroPython-%s" % ubinascii.hexlify(ap_if.config("mac")[-3:])
    ap_if.config(essid=essid, authmode=network.AUTH_WPA_WPA2_PSK, password=b"micropythoN")

def check_bootsec():
    buf = bytearray(bdev.SEC_SIZE)
    bdev.readblocks(0, buf)
    empty = True
    for b in buf:
        if b != 0xff:
            empty = False
            break
    if empty:
        return True
    fs_corrupted()

def fs_corrupted():
    import time
    while 1:
        print("""\
The FAT filesystem starting at sector %d with size %d sectors appears to
be corrupted. If you had important data there, you may want to make a flash
snapshot to try to recover it. Otherwise, perform factory reprogramming
of MicroPython firmware (completely erase flash, followed by firmware
programming).
""" % (bdev.START_SEC, bdev.blocks))
        time.sleep(3)

def setup():
    check_bootsec()
    print("Performing initial setup")
    wifi()
    uos.VfsFat.mkfs(bdev)
    vfs = uos.VfsFat(bdev)
    uos.mount(vfs, '/flash')
    uos.chdir('/flash')
    with open("webrepl_cfg.py", "w") as f1:
        f1.write("""\
PASS = 'micropythoN'
""")
    with open("boot.py", "w") as f2:
        f2.write("""\
# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import gc
import webrepl
import network

gc.collect()

webrepl.start()

gc.collect()

if_cli = network.WLAN(network.STA_IF)
if_cli.active(True)
if_cli.connect('MyWifi', 'MyWifiPassword')

if_ap = network.WLAN(network.AP_IF)

# Rename to standard names:
sta_if = if_cli
ap_if = if_ap

# Function to get IF status.
def ifstatus():
    print(if_cli.ifconfig())
    print(if_ap.ifconfig())

gc.collect()
""")
    return vfs
