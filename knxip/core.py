"""KNX core module

This implements some core KNX classes and methods.
"""
import re
from knxip.helper import tohex


def parse_group_address(addr):
    """Parse KNX group addresses and return the address as an integer.

    This allows to convert x/x/x and x/x address syntax to a numeric
    KNX group address
    """
    res = None

    if re.match('[0-9]+$', addr):
        res = int(addr)

    m = re.match("([0-9]+)/([0-9]+)$", addr)
    if m:
        main = m.group(1)
        sub = m.group(2)
        res = int(main)*256+int(sub)

    m = re.match("([0-9]+)/([0-9]+)/([0-9]+)$", addr)
    if m:
        main = m.group(1)
        middle = m.group(2)
        sub = m.group(3)
        res = int(main)*256*8+int(middle)*256+int(sub)

    if res is None:
        raise KNXException("Address {} does not match any address scheme".
                           format(addr))

    return res


class ValueCache():

    values = {}

    def __init__(self):
        pass

    def get(self, name):
        return self.values.get(name)

    def set(self, name, value):
        old_val = self.values.get(name)
        if old_val != value:
            self.values[name] = value
            return True
        else:
            return False


class KNXException(Exception):

    def __init__(self, message):
        super(KNXException, self).__init__(message)


class KNXMessage(object):

    repeat = 0
    priority = 3 # (0 = system, 1 - alarm, 2 - high, 3 - normal)
    src_addr = 0
    dst_addr = 0
    dt = 0
    routing = 1
    length = 1
    data = [0]
    multicast = 1

    def __init__(self):
        pass

    def sanitize(self):
        self.repeat = self.repeat % 2
        self.priority = self.priority % 4
        self.src_addr = self.src_addr % 0x10000
        self.dst_addr = self.dst_addr % 0x10000
        self.multicast = self.multicast % 2
        self.routing = self.routing % 8
        self.length = self.length % 16
        for i in range(0, self.length-1):
            self.data[i] = self.data[i] % 0x100

    def to_frame(self):
        self.sanitize()
        res = []
        res.append((1 << 7) + (1 << 4) + (self.repeat << 5) +
                   (self.priority << 2))
        res.append(self.src_addr >> 8)
        res.append(self.src_addr % 0x100)
        res.append(self.dst_addr >> 8)
        res.append(self.dst_addr % 0x100)
        res.append((self.multicast << 7) + (self.routing << 4) + self.length)

        for i in range(0, self.length-1):
            res.append(self.data[i])

        checksum = 0
        for i in range(0, 5+self.length):
            checksum += res[i]

        res.append(checksum % 0x100)

        return bytearray(res)

    @classmethod
    def from_frame(cls, frame):
        m = cls()

        # Check checksum first
        checksum = 0
        for i in range(0, len(frame)-1):
            checksum += frame[i]

        if (checksum % 0x100) != frame[len(frame)-1]:
            raise KNXException('Checksum error in frame {}, expected {} but got {}'
                               .format(tohex(frame), frame[len(frame)-1],
                                       checksum % 0x100))

        m.repeat = (frame[0] >> 5) & 0x01
        m.priority = (frame[0] >> 2) & 0x03
        m.src_addr = (frame[1] << 8) + frame[2]
        m.dst_addr = (frame[3] << 8) + frame[4]
        m.multicast = (frame[5] >> 7)
        m.routing = (frame[5] >> 4) & 0x03
        m.length = frame[5] & 0x0f
        m.data = frame[6:-1]

        if len(m.data)+1 != m.length:
            raise KNXException('Frame {} has not the correct length'.format(tohex(frame)))

        return m

        