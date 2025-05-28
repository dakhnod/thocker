import smbus2
import time
import struct
import subprocess
import numpy
import argparse

parser = argparse.ArgumentParser(description='Thermal Camera Person Detection')
parser.add_argument('--verbose', '-v', help='Display the warm pixel count', action='store_true')
parser.add_argument('--bus', '-b', type=int, required=True, help='I2C bus number (default: 7)')
parser.add_argument('--threshold', '-t', type=int, default=5, help='Warm pixel temp threshold')
parser.add_argument('--count', '-c', type=int, default=4, help='Warm pixel count threshold')
parser.add_argument('--cmd-absence', '-a', type=str, default=[], help='Command to run when no person is detected', action='append')
parser.add_argument('--cmd-presence', '-p', type=str, default=[], help='Command to run when a person is detected', action='append')

args = parser.parse_args()

bus = smbus2.SMBus(args.bus)

bus.write_byte_data(0x69, 0, 0x00)
bus.write_byte_data(0x69, 1, 0x3F)
bus.write_byte_data(0x69, 3, 0x00)
bus.write_byte_data(0x69, 2, 0x01)
bus.write_byte_data(0x69, 7, 1 << 5)

time.sleep(0.1)

# Constants for the pixel display
PIXEL_SIZE = 1200  # Size of each pixel in pixels
GRID_SIZE = 8    # 8x8 grid

# Create the main window

last_person_count = 1

# img = numpy.zeros((8, 8), dtype=numpy.uint8)

"""
params = cv2.SimpleBlobDetector_Params()
params.filterByCircularity = False
params.filterByConvexity = False
params.filterByInertia = False
params.filterByColor = False      # Filter by color
params.filterByArea = True       # Filter blobs by area
params.minArea = 5               # Minimum area

blob_detector = cv2.SimpleBlobDetector_create(params)

"""
    
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
                pass
                # img[x, y] = 0
            else:
                # img[x, y] = 255
                warm_pixels += 1
                # relative = temp / max_temp
                # img[x, y] = int(relative * 127 + 128)

    if args.verbose:
        print(f'Warm pixels: {warm_pixels}')

    # cv2.imshow("Thermal Image", img)
    # cv2.waitKey(1)

    # person_count = len(blobs)

    person_count = 1 if (warm_pixels > args.count) else 0

    if person_count is not last_person_count:
        last_person_count = person_count

        print(f'Person present: {person_count}')

        if person_count == 0:
            for cmd in args.cmd_absence:
                subprocess.run(cmd, shell=True)
            # input()
        elif person_count == 1:
            for cmd in args.cmd_presence:
                subprocess.run(cmd, shell=True)

    try:
        time.sleep(1)
    except:
        # cv2.destroyAllWindows()
        break
