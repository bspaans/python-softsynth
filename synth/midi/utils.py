import binascii

def bytes_to_int(bytes):
    return int(binascii.b2a_hex(bytes), 16)

def parse_varbyte_as_int(fp, return_bytes_read=True):
    """Read a variable length of bytes from the file and return the
    corresponding integer."""
    result = 0
    bytes_read = 1
    result = bytes_to_int(fp.read(1))
    if result & 0x80:
        v = result
        result = result & 0x7f
        while v & 0x80:
            v = bytes_to_int(fp.read(1))
            result = (result << 7) + (v & 0x7f)
            bytes_read += 1
    return (result, bytes_read)

