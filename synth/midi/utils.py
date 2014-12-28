import binascii

def bytes_to_int(bytes):
    return int(binascii.b2a_hex(bytes), 16)

def parse_varbyte_as_int(fp, return_bytes_read=True):
    """Read a variable length of bytes from the file and return the
    corresponding integer."""
    result = 0
    bytes_read = 0
    r = 0x80
    while r & 0x80:
        r = bytes_to_int(fp.read(1))
        if r & 0x80:
            result = (result << 7) + (r & 0x7F)
        else:
            result = (result << 7) + r
        bytes_read += 1
    return (result, bytes_read)

