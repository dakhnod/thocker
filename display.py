import smbus2
import time
import struct
import subprocess
import numpy
import argparse
import cv2

parser = argparse.ArgumentParser(description='Thermal Camera Person Detection')
parser.add_argument('--bus', '-b', required=True, help='I2C bus number path')
parser.add_argument('--threshold', '-t', type=int, default=5, help='Warm pixel temp threshold')
args = parser.parse_args()

bus = smbus2.SMBus(args.bus)

bus.write_byte_data(0x69, 0, 0x00)
bus.write_byte_data(0x69, 1, 0x3F)
bus.write_byte_data(0x69, 3, 0x00)
bus.write_byte_data(0x69, 2, 0x01)
bus.write_byte_data(0x69, 7, 1 << 5)

time.sleep(0.1)

last_person_count = 1

img = numpy.zeros((8, 8), dtype=numpy.uint8)
    
while True:
    pixel_count = 64
    data = []
    read_count = 0
    chunk_size = 16
    while read_count < 128:
        data += bus.read_i2c_block_data(0x69, 0x80 + read_count, chunk_size)
        read_count += chunk_size
    temps = struct.unpack('<' + ('h' * pixel_count), bytes(data))
    temps = [i / 4 for i in temps]
    
    min_temp = min(temps)

    normalized = [(i - min_temp) for i in temps]

    max_temp = max(normalized)

    if min_temp == max_temp:
        time.sleep(0.1)
        continue

    def get_temp(x, y):
        return normalized[63 - (y + x * 8)]
    
    warm_pixels = 0
    
    for x in range(8):
        for y in range(8):
            temp = get_temp(y, x)
            if temp < args.threshold:
                img[x, y] = 0
            else:
                img[x, y] = 255

    cv2.imshow("Thermal Image", img)
    cv2.waitKey(1)


    try:
        time.sleep(1)
    except:
        cv2.destroyAllWindows()
        break
