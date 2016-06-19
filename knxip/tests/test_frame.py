import unittest
import ipaddress
from knxip.frame import *


class TestHostProtocolAddressInformation(unittest.TestCase):
    """Testing HostProtocolAddressInformation Factory Class"""
    def test_bytes(self):
        """Testing the .__bytes__"""
        self.assertEquals(bytes((HostProtocolAddressInformation("192.168.2.1",10,HostProtocolCode.IPV4_UDP))),
                          bytes(b'\x08\x01\xc0\xa8\x02\x01\x00\n'))

    def test_PackUnpack(self):
        """Test if To Binary and from Binary for for this Class"""
        self.assertEquals(
            bytes(HostProtocolAddressInformation("192.168.3.15",10,HostProtocolCode.IPV4_UDP)),
            bytes(HostProtocolAddressInformation.from_bytes(
                bytes(HostProtocolAddressInformation("192.168.3.15",10,HostProtocolCode.IPV4_UDP)))
            ))


class TestTunnelConnectionRequestInformation(unittest.TestCase):
    def test_bytes(self):
        """Testing the .__bytes__"""
        self.assertEqual(
            bytes(TunnelConnectionRequestInformation(TunnelKNXLayer.TUNNEL_LINKLAYER)),
            bytes(b'\x04\x04\x02\x00')
        )

        self.assertEqual(
            bytes(TunnelConnectionRequestInformation(TunnelKNXLayer.TUNNEL_BUSMONITOR)),
            bytes(b'\x04\x04\x80\x00')
        )

        self.assertEqual(
            bytes(TunnelConnectionRequestInformation(TunnelKNXLayer.TUNNEL_RAW)),
            bytes(b'\x04\x04\x04\x00')
        )

        x =KNXNetIPHeader(ServiceTypeIdentifier)


class TextKNXIPHeader(unittest.TestCase):

    def test_bytes(self):
        """Testing the .__bytes__"""

        self.assertEqual(
            bytes( KNXNetIPHeader(ServiceTypeIdentifier.TUNNELING_REQUEST)),
            bytes(b'\x06\x01\x04\x20\x00\x06')
        )

    def test_unpack(self):


        y = KNXNetIPHeader(ServiceTypeIdentifier.TUNNELING_REQUEST);
        x = KNXNetIPHeader.from_bytes(bytes(b'\x06\x01\x04\x20\x00\x06'))

        x = bytes(b'\x06\x01\x04\x20\x00\x06')
        self.assertEqual(bytes(KNXNetIPHeader(ServiceTypeIdentifier.TUNNELING_REQUEST)),
                         bytes(KNXNetIPHeader.from_bytes(
                             bytes(b'\x06\x01\x04\x20\x00\x06')
                         )))






if __name__ == '__main__':
    unittest.main()
