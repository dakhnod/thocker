import smbus2
import time
import struct
import statistics
import subprocess
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

last_person_count = 1


img = numpy.zeros((8, 8), dtype=numpy.uint8)

params = cv2.SimpleBlobDetector_Params()
params.filterByCircularity = False
params.filterByConvexity = False
params.filterByInertia = False
params.filterByColor = False      # Filter by color
params.filterByArea = True       # Filter blobs by area
params.minArea = 5               # Minimum area
blob_detector = cv2.SimpleBlobDetector_create(params)

def set_pixel(x, y, relative):
    pass

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
    
    for x in range(8):
        for y in range(8):
            temp = get_temp(x, y)
            if temp < THRESHOLD:
                img[x, y] = 0
            else:
                img[x, y] = 255
                # relative = temp / max_temp
                # img[x, y] = int(relative * 127 + 128)

    blobs = blob_detector.detect(img)

    # print(img)

    print(blobs)

    im_with_keypoints = cv2.drawKeypoints(img, blobs, numpy.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
 
    # Show keypoints
    cv2.imshow("Keypoints", im_with_keypoints)
    cv2.waitKey(1)

    person_count = len(blobs)

    if person_count is not last_person_count:
        last_person_count = person_count

        print(person_count)

        if person_count == 0:
            subprocess.run(['xdg-screensaver', 'activate'])
            # subprocess.run(['notify-send', 'locked'])
        elif person_count == 1:
            subprocess.run(['ddcutil', 'setvcp', '10', '0'])
        elif person_count == 2:
            subprocess.run('/home/daniel/bin/minimize-chrome')
            subprocess.run(['ddcutil', 'setvcp', '10', '40'])

    try:
        time.sleep(1)
    except:
        cv2.destroyAllWindows()
        break