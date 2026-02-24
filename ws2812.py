import serial
from paho.mqtt import client as mqtt
import json
import time
import threading
import sys

port = serial.Serial('/dev/ttyWS2812')

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

max_brightness = 10

leds_pause_time = 0

LOCK_ICON = [[
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
],
[
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
]]

SMILEY_ICON = [[
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [1, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
],
[
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [1, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
]]

message_mutex = threading.Lock()

def convert_to_payload(icon, color):
    def c(data):
        payload = bytearray()
        for row in data[::-1]:
            for pixel in row:
                if pixel == 0:
                    payload.extend((0, 0, 0))
                else:
                    payload.extend(color)
        return payload
    
    return list(map(c, icon))


LOCK_ICON_PAYLOAD = convert_to_payload(LOCK_ICON, (0, max_brightness, 0))
SMILEY_ICON_PAYLOAD = convert_to_payload(SMILEY_ICON, (max_brightness, 0, 0))

def on_message(client, userdata, msg):
    with message_mutex:
        global leds_pause_time
        if msg.topic == 'sensors/tof/vl53l7cx/ranges_mm':
            if (time.time() - leds_pause_time) < 2:
                return
            payload = json.loads(msg.payload)

            led_data = bytes()

            for i in range(len(payload)):
                r = range(0, len(payload[i])) if (i % 2 == 1) else range(len(payload[i]) - 1, -1, -1)

                for j in r:
                    if payload[i][j] == -1:
                        pixel = (0, 0, 0)
                    elif payload[i][j] > 1000:
                        pixel = (max_brightness, 0, 0)
                    else:
                        normalized = 1 - (payload[i][j] / 1000)
                        # normalized **= 2
                        pixel = (0, int(max_brightness * normalized), int(max_brightness * (1 - normalized)))

                    led_data += bytes(pixel)

            port.write(led_data)
        elif msg.topic == 'sensors/tof/vl53l7cx/person_count':
            time.sleep(0.01)
            person_count = int(msg.payload.decode('utf-8'))
            leds_pause_time = time.time()
            payload = (LOCK_ICON_PAYLOAD if person_count == 0 else SMILEY_ICON_PAYLOAD)

            port.write(bytes(payload[0]))
            time.sleep(0.5)
            port.write(bytes(payload[1]))


client.on_message = on_message
client.on_connect = lambda client, userdata, flags, rc, _: print("Connected with result code " + str(rc))


client.connect('localhost')
client.subscribe('sensors/tof/vl53l7cx/ranges_mm')
client.subscribe('sensors/tof/vl53l7cx/person_count')

client.loop_forever()