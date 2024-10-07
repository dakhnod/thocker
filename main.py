import smbus2
import time
import struct
import statistics

bus = smbus2.SMBus(10)

bus.write_byte_data(0x69, 0, 0x00)
bus.write_byte_data(0x69, 1, 0x3F)
bus.write_byte_data(0x69, 3, 0x00)
bus.write_byte_data(0x69, 2, 0x01)

time.sleep(0.1)

while True:
    pixel_count = 64
    data  = bus.read_i2c_block_data(0x69, 0x80     , 32)
    data += bus.read_i2c_block_data(0x69, 0x80 + 32, 32)
    data += bus.read_i2c_block_data(0x69, 0x80 + 64, 32)
    data += bus.read_i2c_block_data(0x69, 0x80 + 96, 32)
    temps = struct.unpack('<' + ('h' * pixel_count), bytes(data))
    temps = [i / 4 for i in temps]
    
    min_temp = min(temps)
    
    normalized = [i - min_temp for i in temps]
    
    print(sum(normalized))
    time.sleep(1)
print(data)