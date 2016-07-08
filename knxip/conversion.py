from knxip.core import KNXException

def float_to_knx(floatval):
    """Convert a float to a 2 byte KNX float value"""

    if floatval < -671088.64 or floatval > 670760.96:
        raise KNXException("float {} out of valid range".format(floatval))

    floatval = floatval * 100

    for i in range(0, 15):
        exp = pow(2, i)
        if ((floatval / exp) >= -2048) and ((floatval / exp) < 2047):
            break

    if floatval < 0:
        sign = 1
        mantisse = int(2048 + (floatval / exp))
    else:
        sign = 0
        mantisse = int(floatval / exp)

    return [(sign << 7) + (i << 3) + (mantisse >> 8),
            mantisse & 0xff]

