import ipaddress
import ctypes
import struct
from enum import IntEnum

"""
    TODO:
        * Build Test for HostProtocolAddressInformation
        * Implement the other Stuff to Build Easily and KNXIP Frame

"""

class HostProtocolCodes(IntEnum):
    """
    Represent the 2 Possible Host Protocol Codes defined in KNX Standard v2.1 3.8.2-8.6.2

    Info:
    Use it to set the Protocol for a Host Protocol Address Information object
    """
    IPV4_UDP=1
    IPV4_TCP=2

class HostProtocolAddressInformation():
    """
    Represent a Class to Hold and Build a Host Protocol Address Information (HPAI) byte array as defined in KNX Standard v2.1 3.8.2-8.6.2
    """

    host = None
    """ IPv4 Address as String"""

    port = None
    """ UDP Port as Integer """

    hpai_frame_default_size = 0x8
    """ Define Default Frame Size of a HPAI Frame"""

    host_protocol_code = HostProtocolCodes.IPV4_UDP
    """ Protocol Code to Use for this HPAI"""

    def __init__(self,host,port,protocol):
        """
        Create a new Instance of an Host Protocol Address Information Defined in KNX Standard 3.8.2-8.6.2
        :param host: KNX IP Gateway/Router IP Address as String
        :param port: IPv4 Port as Integer
        :param protocol: Host Protocol Code (Use Enum HostProtocolCodes)
        """
        self.host = host
        self.port = port
        self.host_protocol_code = protocol
        pass

    @classmethod
    def from_bytes(cls, bytes):
        """
        Create a new Instance of an Host Protocol Address Information Defined in KNX Standard 3.8.2-8.6.2
        :param bytes: Byte Array of HPAI
        """
        hpai_tuple = struct.unpack('BB4s2s',bytes)
        return cls(
            str(ipaddress.IPv4Address(hpai_tuple [2])),
            (struct.unpack('!H', hpai_tuple[3]))[0],
            hpai_tuple[1]
        )

    @property
    def ipv4_address(self):
        """
        IP Address Object Represantation of the host property
        :return: IPv4Address
        """
        return ipaddress.IPv4Address(self.host)

    @property
    def bytes(self):
        """
        Return the Host Protocol Address Information (HPAI) as byte array
        :return: Bytes
        """
        return struct.pack('BB4s2s',
                           self.hpai_frame_default_size,
                           self.host_protocol_code,
                           self.ipv4_address.packed,
                           struct.pack('!H',self.port)
                           )