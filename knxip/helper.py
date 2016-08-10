"""Helper functions that are not specifically KNX related"""

def tohex(byte_array):
    """Convert a byte array to a HEX string representation."""
    return "".join("%02x " % b for b in byte_array)


def ip_to_array(ipaddress):
    """Convert a string representing an IPv4 address to 4 bytes."""
    res = []
    for i in ipaddress.split("."):
        res.append(int(i))

    assert len(res) == 4
    return res


def int_to_array(i, length=2):
    """Convert an length byte integer to an array of bytes."""
    res = []
    for dummy in range(0, length):
        res.append(i & 0xff)
        i = i >> 8
    return reversed(res)
