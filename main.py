import smbus2
import time
import struct
import statistics
import subprocess
import tkinter
import sys
import cv2
import numpy

THRESHOLD = 5
ROW = 2

bus = smbus2.SMBus(7)

bus.write_byte_data(0x69, 0, 0x00)
bus.write_byte_data(0x69, 1, 0x3F)
bus.write_byte_data(0x69, 3, 0x00)
bus.write_byte_data(0x69, 2, 0x01)
bus.write_byte_data(0x69, 7, 1 << 5)

time.sleep(0.1)

# Constants for the pixel display
PIXEL_SIZE = 120  # Size of each pixel in pixels
GRID_SIZE = 8    # 8x8 grid

# Create the main window
root = tkinter.Tk()
root.title("Thermal Camera")

last_person_count = 1

# Create a Canvas to draw on
canvas = tkinter.Canvas(root, width=PIXEL_SIZE * GRID_SIZE, height=PIXEL_SIZE * GRID_SIZE)
canvas.pack()

def set_pixel(x, y, relative):
    x1 = x * PIXEL_SIZE
    y1 = y * PIXEL_SIZE
    x2 = x1 + PIXEL_SIZE
    y2 = y1 + PIXEL_SIZE
    # Draw a rectangle (pixel)
    canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill=f'#{int(255 * relative):02x}00{int(255 * (1 - relative)):02x}')

while True:
    pixel_count = 64
    data  = bus.read_i2c_block_data(0x69, 0x80     , 32)
    data += bus.read_i2c_block_data(0x69, 0x80 + 32, 32)
    data += bus.read_i2c_block_data(0x69, 0x80 + 64, 32)
    data += bus.read_i2c_block_data(0x69, 0x80 + 96, 32)
    temps = struct.unpack('<' + ('h' * pixel_count), bytes(data))
    temps = [i / 4 for i in temps]
    
    min_temp = min(temps)

    normalized = [(i - min_temp) for i in temps]

    max_temp = max(normalized)

    if min_temp == max_temp:
        time.sleep(0.1)
        continue

    warm_pixels = 0

    def get_temp(x, y):
        return normalized[63 - (y + x * 8)]
    
    for x in range(8):
        for y in range(8):
            temp = get_temp(x, y)
            if temp < 5:
                relative = 0
            else:
                relative = temp / max_temp
                warm_pixels += 1
            try:
                set_pixel(x, y, relative)
            except:
                print('error setting pixel')
                pass

    was_warm = get_temp(0, ROW) > THRESHOLD

    person_count = 1 if was_warm else 0

    for i in range(7):
        temp = get_temp(i, ROW)
        is_warm = temp > THRESHOLD
        if is_warm is not was_warm:
            if is_warm:
                person_count += 1
            was_warm = is_warm

    if person_count is not last_person_count:
        last_person_count = person_count

        print(person_count)

        if person_count == 0:
            # subprocess.run(['xdg-screensaver', 'activate'])
            subprocess.run(['notify-send', 'locked'])
            tkinter.mainloop()
        elif person_count == 1:
            subprocess.run(['ddcutil', 'setvcp', '10', '0'])
        elif person_count == 2:
            subprocess.run('/home/daniel/bin/minimize-chrome')
            subprocess.run(['ddcutil', 'setvcp', '10', '40'])

    root.update_idletasks()
    root.update()
    
    time.sleep(1)