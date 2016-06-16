import unittest
import ipaddress
from knxip.frame import *

class Test_HostProtocolAddressInformation(unittest.TestCase):
    """Testing HostProtocolAddressInformation Factory Class"""
    def test_bytes(self):
        """Testing the .bytes"""
        self.assertEquals((HostProtocolAddressInformation("192.168.2.1",10,HostProtocolCodes.IPV4_UDP).bytes),bytes(b'\x08\x01\xc0\xa8\x02\x01\x00\n'))

    def test_PackUnpack(self):
        """Test if To Binary and from Binary for for this Class"""
        self.assertEquals(HostProtocolAddressInformation("192.168.3.15",10,HostProtocolCodes.IPV4_UDP).bytes,
                          HostProtocolAddressInformation.from_bytes(
                              HostProtocolAddressInformation("192.168.3.15",10,HostProtocolCodes.IPV4_UDP).bytes
                          ).bytes)


if __name__ == '__main__':
    unittest.main()
