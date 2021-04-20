# Bluetooth Low Energy (BLE) scanner to find Apple Watch

Proof of concept Bluetooth Low Energy (BLE) scanner to detect Apple Watch, even with Apple's MAC address randomisation.

Once an Apple Watch has been detected the MAC address is tracked and the RSSI (signal strength) is published to an MQTT topic.

Home Automation presence detection software can track the RSSI of the watch and determine which room you are in. This can be used for automations.

A project to do room presence detection is my [presence-ml]() project. Using multiple, even overlapping, scanners it can predict which room you are in, based on tracking your device.

## How to load this on to an ESP32
See my intro to ESP's from [Google DevFest 2020](https://github.com/dalehumby/DevFest2020) that explains how to flash MicroPython on to an ESP8266 or ESP32. (Note that you need to use an ESP32 for this project as the ESP8266 does _not_ have Bluetooth.)

Once you have MicroPython installed on the device, use `ampy` to copy 
- boot.py
- main.py
- config.json (Change the details of this file to suit your home network)
- umqttsimple.py

Restart the device and you should start seeing RSSI messages being published to the MQTT broker. Connect to the REPL over USB serial to see diagnostic output.

## Todo's
- [ ] Remove hardcoded watch ID `dale_apple_watch` and track eg `Watch3,3`
- [ ] Connect to the suspected Apple Watch and determine the Model Number characteristic
- [ ] Test with other Apple Watch models
- [ ] Implement the [room-assistant-companion](https://github.com/mKeRix/room-assistant-companion-ios) protocol, so that you can track your Apple iPhone
- [ ] This code should eventually be ported to the ESPHome project, the world doesn't need another RSSI project

## Tested with
- MicroPython 1.14
- Generic MINI32 board (ESP32 with integrated 5V to 3V and USB to serial converter)
- Apple Watch Series 3 (`Watch3,3`)

## Prior work on fingerprinting Apple device
- [Apple device continuity](https://github.com/furiousMAC/continuity)
- https://petsymposium.org/2020/files/papers/issue1/popets-2020-0003.pdf
- https://arxiv.org/pdf/1703.02874.pdf
- https://samteplov.com/uploads/shmoocon20/slides.pdf
- https://i.blackhat.com/eu-19/Thursday/eu-19-Yen-Trust-In-Apples-Secret-Garden-Exploring-Reversing-Apples-Continuity-Protocol-3.pdf

## Similar projects
- [ESPHome BLE RSSI sensor](https://esphome.io/components/sensor/ble_rssi.html)
- [room-assistant](https://www.room-assistant.io/guide/)
- [ESP32-mqtt-room](https://github.com/jptrsn/ESP32-mqtt-room)
