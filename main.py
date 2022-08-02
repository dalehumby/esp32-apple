"""
Proof of concept Bluetooth Low Energy (BLE) scanner to detect Apple Watch,
even with Apple's MAC adddress randomisation.

Publishes to MQTT topic `{station_id}/sensors/dale_apple_watch/rssi`.
This is the same format as the ESPHome MQTT message for RSSI sensors.

TODO's
- [ ] Remove hardcoded watch ID `dale_apple_watch` and track eg `Watch3,3`
- [ ] This code should eventually be ported to the ESPHome project

Tested with
- MicroPython 1.14
- Generic MINI32 board (ESP32 with integrated 5V to 3V and USB to serial converter)
- Apple Watch Series 3 (Watch3,3)
"""

import esp
import network
import ubluetooth
import ujson as json
import utime as time
from machine import Timer, freq, reset
from micropython import alloc_emergency_exception_buf, const, schedule

from umqttsimple import MQTTClient

_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
watch_addr = None


class Filter:
    """
    Low pass software filter using the Exponential Weighted Function
    (or Infinite Impulse Response) filtering method.
    """

    def __init__(self, init_value, n):
        self.n = n
        self.sum = init_value * n

    def update(self, value):
        average = self.sum / self.n
        self.sum = self.sum - average + value
        return self.sum / self.n


def mqtt_pub(args):
    device_id, rssi = args
    """
    Periodically publish metrics to MQTT.
    """
    # print("Pubishing to MQTT")
    try:
        mqtt.publish(
            b"%s/sensor/%s/state" % (config["station_id"], device_id),
            bytes(str(rssi), "utf-8"),
        )
    except OSError as e:
        print("MQTT error:", e)
        mqtt.connect()


def hex(bytes):
    """Change bytes to printable hex string."""
    res = ""
    for b in bytes:
        res += "%02x" % b
    return res


def watchdog_expired(t):
    """Restart the CPU if the timer expires."""
    global watchdog
    print("Watchdog timer expired, restarting CPU...")
    watchdog.deinit()
    reset()


def restart_watchdog():
    """Restart the watchdog timer. CPU resets if timer is not called often."""
    global watchdog
    watchdog.init(period=30000, mode=Timer.ONE_SHOT, callback=watchdog_expired)


# Setup 2 low pass filters
watch_rssi1 = Filter(-70, 2)
watch_rssi2 = Filter(-70, 3)


def ble_handler(event, data):
    """
    Handle the Bleutooth events.
    """
    global watch_addr
    global watch_rssi1
    global watch_rssi2
    if event == _IRQ_SCAN_RESULT:
        restart_watchdog()
        (addr_type, addr, adv_type, rssi, adv_data) = data
        # print(bytes(addr))
        addr = hex(bytes(addr))
        adv_data = hex(bytes(adv_data))
        rssi = int(rssi)
        if addr == "49bac8fb5a6f":
            print(addr_type, addr, adv_type, rssi, adv_data)
        if adv_data[16:28] == "4c0010050198" or addr == watch_addr:
            # print("Found Apple Watch")
            # TODO connect to Apple Watch and check that the "Device Information" service
            # has the characteristic "Model Number" "Watch3,3"
            watch_addr = addr
            rssi = watch_rssi1.update(rssi)
            rssi = watch_rssi2.update(rssi)
            schedule(mqtt_pub, ("dale_apple_watch_rssi", int(rssi)))
        elif addr == "d9d799bff3d1":
            print("Found sticknfind")
            schedule(mqtt_pub, ("sticknfind_rssi", rssi))
    elif event == _IRQ_SCAN_DONE:
        print("Scan done")
    else:
        print("Unknown event:", event, data)
        print(type(event))


esp.osdebug(None)
alloc_emergency_exception_buf(100)
freq(240000000)

# Setup watchdog timer
watchdog = Timer(0)
restart_watchdog()

# Wait before registering interrupts and timers
print(
    "Waiting 2s before starting up... press CTRL+C to get REPL and stop the watchdog timer"
)
time.sleep(2)

with open("config.json", "r") as f:
    config = json.load(f)


# Setup Wifi
print("Connecting to wifi...")
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(config["wifi"]["ssid"], config["wifi"]["password"])
while not station.isconnected():
    pass
print("Connected to wifi")


# Setup MQTT
mqtt = MQTTClient(
    config["station_id"],
    config["mqtt"]["server"],
    user=config["mqtt"]["username"],
    password=config["mqtt"]["password"],
)
mqtt.connect()
print("Connected to MQTT")

# Setup Bluetooth
ble = ubluetooth.BLE()
ble.config(rxbuf=2000)
ble.irq(ble_handler)
ble.active(True)


print("Activating Bluetooth scan...")

try:
    ble.gap_scan(0, 1280000, 500000)  # Deault scan window of 1.28s, but scan for 500ms
    while True:
        pass
except Exception as e:
    print("Error:", e)
    reset()
