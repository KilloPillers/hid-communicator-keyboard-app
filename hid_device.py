import sys
import hid
import bmp
import time

vendor_id     = 0x4273
product_id    = 0x7563

usage_page    = 0xFF60
usage         = 0x61
report_length = 32

def reverse_bits(byte) -> int:
    return int('{:08b}'.format(byte)[::-1], 2)


def flip_vertical(byteArray: bytearray, width=128, height=32) -> bytearray:
    """Flip image across vertical axis (mirror left <-> right)."""
    flipped = bytearray(len(byteArray))
    width_bytes = width // 8

    for y in range(height):
        for x in range(width):
            byte_index = (y * width_bytes) + (x // 8)
            bit_index = 7 - (x % 8)
            bit = (byteArray[byte_index] >> bit_index) & 1

            # Flipped x coordinate
            new_x = width - 1 - x
            new_byte_index = (y * width_bytes) + (new_x // 8)
            new_bit_index = 7 - (new_x % 8)

            if bit:
                flipped[new_byte_index] |= (1 << new_bit_index)

    return flipped

def flip_horizontal(byteArray: bytearray, width=128, height=32) -> bytearray:
    """Flip image across horizontal axis (mirror top <-> bottom)."""
    flipped = bytearray(len(byteArray))
    width_bytes = width // 8

    for y in range(height):
        for x in range(width):
            byte_index = (y * width_bytes) + (x // 8)
            bit_index = 7 - (x % 8)
            bit = (byteArray[byte_index] >> bit_index) & 1

            # Flipped y coordinate
            new_y = height - 1 - y
            new_byte_index = (new_y * width_bytes) + (x // 8)
            new_bit_index = 7 - (x % 8)

            if bit:
                flipped[new_byte_index] |= (1 << new_bit_index)

    return flipped


def transform_data_for_lcd(byteArray, inverted=False) -> bytearray:
    width = 128
    height = 32

    transformed_data = bytearray()
    width_bytes = width // 8
    pages = height // 8        # vertical pages
    for page in range(pages):
        for x in range(width):
            byte = 0
            for bit in range(8):
                y = page * 8 + bit
                row_index = y * width_bytes
                byte_index = row_index + x // 8
                bit_index = 7 - (x % 8)
                if byteArray[byte_index] & (1 << bit_index):
                    byte |= (1 << bit)

            byte = (~byte & 0xFF) if inverted else byte

            transformed_data.append(byte)

    return transformed_data

def get_raw_hid_interface():
    device_interfaces = hid.enumerate(vendor_id, product_id)
    raw_hid_interfaces = [i for i in device_interfaces if i['usage_page'] == usage_page and i['usage'] == usage]

    if len(raw_hid_interfaces) == 0:
        return None

    interface = hid.Device(path=raw_hid_interfaces[0]['path'])

    print(f"Manufacturer: {interface.manufacturer}")
    print(f"Product: {interface.product}")

    return interface

def send_raw_report(data):
    interface = get_raw_hid_interface()

    if interface is None: 
        print("No device found")
        sys.exit(1)


    header_bytes = 2 # 1 for id code another for length of payload
    offset = 0

    for i in range(18):
        ## Creat request report
        data_length = min(512-offset, 30)

        request_data = [0x00] * (header_bytes + 1) # First byte is Report ID always 0x00 this device
        request_data[1] = 0x09 # id_code (arbitrary, one of several id codes available)
        request_data[2] = data_length   # length of the data
        request_report = bytearray(request_data) # convert to byte array
        request_report.extend(data[offset:offset + data_length]) # add payload
        offset += data_length # increment offset
        ###

        try:
            interface.write(bytes(request_report))

            response_report = interface.read(report_length, timeout=1000)
        except:
            interface.close()

    interface.close()

if __name__ == '__main__':
    width, height, img_data = bmp.load("test.bmp")
    width_bytes = width // 8
    pages = height // 8        # vertical pages
    print(f"width: {width} height: {height}")
    ## transform data into a form the hardware can use
    transformed_data = bytearray()

    inverted = True
    flipped = False
    for page in range(pages):
        for x in range(width):
            byte = 0
            for bit in range(8):
                y = page * 8 + bit
                row_index = y * width_bytes
                byte_index = row_index + x // 8
                bit_index = 7 - (x % 8)
                if img_data[byte_index] & (1 << bit_index):
                    byte |= (1 << bit)

            byte = (~byte & 0xFF) if inverted else byte

            transformed_data.append(byte)
    
    send_raw_report(transformed_data)