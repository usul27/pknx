import ipaddress
import ctypes
import struct
from enum import Enum

"""
    TODO:
        * Build Test for HostProtocolAddressInformation
        * Build Test for HostProtocolCodes
        * Implement the other Stuff to Build Easily and KNXIP Frame

"""

class HostProtocolCodes(Enum):
    """
    Represent the 2 Possible Host Protocol Codes defined in KNX Standard v2.1 3.8.2-8.6.2

    Info:
    Use it to set the Protocol for a Host Protocol Address Information object
    """
    IPV4_UDP=0x1
    IPV4_TCP=0x2

class HostProtocolAddressInformation():
    """
    Represent a Class to Hold and Build a Host Protocol Address Information (HPAI) byte array as defined in KNX Standard v2.1 3.8.2-8.6.2
    """

    host = None
    port = None
    hpai_frame_default_size = 0x8
    host_protocol_code = HostProtocolCodes.IPV4_UDP

    def __init__(self,host,port,protocol):
        """
        Create a new Instance of an Host Protocol Address Information Defined in KNX Standard 3.8.2-8.6.2
        :param host: KNX IP Gateway/Router IP Address as String
        :param port: IPv4 Port as Integer
        :param protocol: Host Protocol Code (Use Enum HostProtocolCodes)
        """
        self.__host = host
        self.__port = port
        self.__host_protocol_code = protocol
        pass

    @classmethod
    def unpack(cls, bytes):
        """
        Create a new Instance of an Host Protocol Address Information Defined in KNX Standard 3.8.2-8.6.2
        :param bytes: Byte Array of HPAI
        """
        hpai_tulpe = struct.unpack('ccih',bytes)
        hpai_proto = hpai_tulpe[1]
        binaryIp = hpai_tulpe[2]
        port = hpai_tulpe[3]
        return cls()

    @property
    def ipv4_address(self):
        """
        IP Address Object Represantation of the host property
        :return: IPv4Address
        """
        return ipaddress.IPv4Address(self.host)

    @property
    def to_bytes(self):
        """
        Return the Host Protocol Address Information (HPAI) as byte array
        :return: bytearray
        """
        return struct.pack('ccih',
                           self.__hpai_frame_default_size,
                           self.__host_protocol_code,
                           self.ipaddress.packed,
                           ctypes.c_ushort(self.port)
                           )