import sys
import hid
import bmp

vendor_id     = 0x4273
product_id    = 0x7563

report_length = 32

def reverse_bits(byte) -> int:
    """Reverse the order of bits in a byte e.g. 00000001 -> 10000000"""
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
    """Turns data from row-major to page major format"""
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
    print("Opening the device")
    
    try:
        interface = hid.device()
        interface.open(vendor_id, product_id)  # Boarsource/unicorne VendorID/ProductID

        print("Manufacturer: %s" % interface.get_manufacturer_string())
        print("Product: %s" % interface.get_product_string())
        print("Serial No: %s" % interface.get_serial_number_string())
        
        interface.set_nonblocking(1)
        
        return interface
    except:
        return None

    return None


def send_raw_report(interface, data, include_report_id=True):
    """
    Sends 32-byte HID reports. If include_report_id=True, prepends 0x00 as the first byte
    (for Windows hidapi compatibility).
    """
    REPORT_SIZE = 32
    HEADER_BYTES = 3  # id_code + length + maybe report ID
    ID_CODE = 0x09

    offset = 0
    while offset < len(data):
        data_length = min(len(data) - offset, REPORT_SIZE - HEADER_BYTES)
        payload = bytearray([ID_CODE, data_length])
        payload.extend(data[offset:offset + data_length])
        payload.extend([0x00] * (REPORT_SIZE - len(payload)))

        if include_report_id:
            report = bytearray([0x00])  # prepend report ID=0
            report.extend(payload)
        else:
            report = payload

        try:
            res = interface.write(bytes(report))
        except Exception as e:
            interface.close()
            return

        offset += data_length


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

    interface = get_raw_hid_interface()
    send_raw_report(interface, transformed_data)
