import ipaddress
import ctypes
import struct
from enum import IntEnum

KNXIP_PROTOCOL_VERSION = 0x1  # Define the Protocol Version for all Factory Classes


"""
    TODO:
        * Build Test for HostProtocolAddressInformation
        * Implement the other Stuff to Build Easily and KNXIP Frame

"""


class ServiceTypeIdentifier(IntEnum):
    """ Represent a KNXNet/IP Service Type Identifier defined in KNX Standard v2.1 3.8.1 - 5.3"""

    """
    Core Service Identifiers
    ====================================================================================================================
    """

    SEARCH_REQUEST = 0x0201
    """Sent by KNXNet/IP Client to search available KNXNet/IP Servers"""

    SEARCH_RESPONSE = 0x0202
    """Sent by KNXNet/IP Server when receiving a KNXNet/IP SEARCH_REQUEST"""

    DESCRIPTION_REQUEST = 0x0203
    """Sent by KNXNet/IP Client to a KNXNet/IP Server to retrieve information
    about capabilities and supported services"""

    DESCRIPTION_RESPONSE = 0x0204
    """Sent by KNXNet/IP Server in response to a DESCRIPTION_REQUEST to
        provide information about the server implementation"""

    CONNECT_REQUEST = 0x0205
    """Sent by KNXNet/IP Client for establishing a communication channel to a KNXNet/IP Server"""

    CONNECT_RESPONSE = 0x0206
    """Sent by KNXNet/IP Server as answer to CONNECT_REQUEST telegram"""

    CONNECTIONSTATE_REQUEST = 0x0207
    """Sent by KNXNet/IP Client for requesting the connection state of an
    established connection to a KNXNet/IP Server"""

    CONNECTIONSTATE_RESPONSE = 0x0208
    """Sent by KNXNet/IP Server when receiving a CONNECTIONSTATE_REQUEST for an established connection"""

    DISCONNECT_REQUEST = 0x0209
    """Sent by KNXNet/IP device, typically the KNXNet/IP Client, to terminate an established connection"""

    DISCONNECT_RESPONSE = 0x020A
    """Sent by KNXNet/IP device, typically the KNXNet/IP Server, in response to a DISCONNECT_REQUEST"""

    """
    Device Management Service Identifiers
    ====================================================================================================================
    """

    DEVICE_CONFIGURATION_REQUEST = 0x0310
    """Reads/Writes KNXNet/IP device configuration data (Interface Object Properties)"""

    DEVICE_CONFIGURATION_ACK = 0x0311
    """Sent by a KNXNet/IP device to confirm the reception of the DEVICE_CONFIGURATION_REQUEST"""

    """
    Tunneling Service Identifiers
    ====================================================================================================================
    """

    TUNNELING_REQUEST = 0x0420
    """Used for sending and receiving single KNX telegrams between KNXnet/IP Client and - Server"""

    TUNNELING_ACK = 0x0421
    """Sent by a KNXNet/IP device to confirm the reception of the TUNNELING_REQUEST"""

    """
    Routing Service Identifiers
    ====================================================================================================================
    """

    ROUTING_INDICATION = 0x0530
    """Used for sending KNX telegrams over IP networks. This service is unconfirmed"""

    ROUTING_LOST_MESSAGE = 0x0531
    """Used for indication of lost KNXNet/IP Routing messages. This service is unconfirmed"""


class ConnectionType(IntEnum):
    """Represent a KNXNet/IP Connection Types Identifier defined in KNX Standard v2.1 3.8.1 - 5.4"""

    DEVICE_MGMT_CONNECTION = 0x03
    """Data connection used to configure a KNXNet/IP device"""

    TUNNEL_CONNECTION = 0x04
    """Data connection used to forward KNX telegrams between two KNXNet/IP devices"""

    REMLOG_CONNECTION = 0x06
    """Data connection used for configuration and data transfer with a remote logging server"""

    REMCONF_CONNECTION = 0x07
    """Data connection used for data transfer with a remote configuration server"""

    OBJSVR_CONNECTION = 0x08
    """Data connection used for configuration and data transfer with an Object Server in a KNXnet/IP device"""


class CommonErrorCode(IntEnum):
    """Represent a KNXNet/IP error code defined in KNX Standard v2.1 3.8.1 - 5.5.1"""

    E_NO_ERROR = 0x00
    """Operation successful"""

    E_HOST_PROTOCOL_TYPE = 0x01
    """The requested host protocol is not supported by the KNXNet/IP device"""

    E_VERSION_NOT_SUPPORTED = 0x02
    """The requested protocol version is not supported by the KNXNet/IP device"""

    E_SEQUENCE_NUMBER = 0x04
    """The received sequence number is out of order"""

    def __str__(self):
        """Return the Common error code Text as String"""
        if self.value == CommonErrorCode.E_NO_ERROR:
            return "Operation successful"
        elif self.value == CommonErrorCode.E_HOST_PROTOCOL_TYPE:
            return "The requested host protocol is not supported by the KNXNet/IP device"
        elif self.value == CommonErrorCode.E_VERSION_NOT_SUPPORTED:
            return "The requested protocol version is not supported by the KNXNet/IP device."
        elif self.value == CommonErrorCode.E_SEQUENCE_NUMBER:
            return "The received sequence number is out of order"
        else:
            raise ValueError("Invalid CommonErrorCodes Value")


class ConnectionResponseCode(IntEnum):
    """Represent a KNXNet/IP Connection Response Status code defined in KNX Standard v2.1 3.8.1 - 5.5.2"""

    E_NO_ERROR = 0x00
    """The connection is established successfully"""

    E_CONNECTION_TYPE = 0x22
    """The KNXNet/IP Server device does not support the requested connection type"""

    E_CONNECTION_OPTION = 0x23
    """The KNXNet/IP Server device does not support one or more requested connection options"""

    E_NO_MORE_CONNECTIONS = 0x24
    """The KNXNet/IP Server device cannot accept the new data connection because its
    maximum amount of concurrent connections is already used."""

    def __str__(self):
        """Return the Connection Response Code Text as string"""
        if self.value == ConnectionResponseCode.E_NO_ERROR :
            return "The connection is established successfully"
        elif self.value == ConnectionResponseCode.E_CONNECTION_TYPE:
            return "The KNXNet/IP Server device does not support the requested connection type"
        elif self.value == ConnectionResponseCode.E_CONNECTION_OPTION:
            return "The KNXNet/IP Server device does not support one or more requested connection options"
        elif self.value == ConnectionResponseCode.E_NO_MORE_CONNECTIONS:
            return "The KNXNet/IP Server device cannot accept the new data connection because its maximum amount of concurrent connections is already used."
        else:
            raise ValueError("Invalid ConnectionResponseCode")


class ConnectionStateResponseCode(IntEnum):
    """Represent a KNXNet/IP Connection Response Status code defined in KNX Standard v2.1 3.8.1 - 5.5.3"""

    E_NO_ERROR = 0x0
    """The connection state is normal"""

    E_CONNECTION_ID = 0x21
    """The KNXNet/IP Server device cannot find an active data connection with the specified ID"""

    E_DATA_CONNECTION = 0x26
    """The KNXNet/IP Server device detects an error concerning the data connection with the specified ID"""

    E_KNX_CONNECTION = 0x27
    """The KNXNet/IP Server device detects an error concerning the KNX connection with the specified ID"""

    def __str__(self):
        """Return the Connection State Response Code Text as string"""
        if self.value == ConnectionStateResponseCode.E_NO_ERROR:
            return "The connection state is normal"
        elif self.value == ConnectionStateResponseCode.E_CONNECTION_ID:
            return "The KNXNet/IP Server device cannot find an active data connection with the specified ID"
        elif self.value == ConnectionStateResponseCode.E_DATA_CONNECTION:
            return "The KNXNet/IP Server device detects an error concerning the data connection with the specified ID"
        elif self.value == ConnectionStateResponseCode.E_KNX_CONNECTION:
            return "The KNXNet/IP Server device detects an error concerning the KNX connection with the specified ID"
        else:
            raise ValueError("Invalid ConnectionStateResponseCode")


class TunnelConnectionAckCode(IntEnum):
    """Represent a KNXNet/IP Tunnel Ack code defined in KNX Standard v2.1 3.8.1 - 5.5.4"""

    E_NO_ERROR = 0x0
    """The message is received successfully"""

    E_TUNNELING_LAYER = 0x29
    """The KNXNet/IP Server device does not support the requested KNXNet/IP Tunnelling layer"""

    def __str__(self):
        """Return the Tunnel Connection ACK Error Code Text as string"""
        if self.value == TunnelConnectionAckCode.E_NO_ERROR:
            return "The message is received successfully"
        elif self.value == TunnelConnectionAckCode.E_TUNNELING_LAYER:
            return "The KNXNet/IP Server device does not support the requested KNXNet/IP Tunnelling layer"
        else:
            raise ValueError("Invalid TunnelConnectionAckCode")

class HostProtocolCode(IntEnum):
    """
    Represent the 2 Possible Host Protocol Codes defined in KNX Standard v2.1 3.8.2 - 8.6.2

    Info:
    Use it to set the Protocol for a Host Protocol Address Information object
    """
    IPV4_UDP = 1
    IPV4_TCP = 2


class HostProtocolAddressInformation():
    """
    Represent a Class to Hold and Build a Host Protocol Address Information (HPAI) byte array as defined in KNX Standard v2.1 3.8.2 - 8.6.2
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

    def __bytes__(self):
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


class CommunicationChannelConnectionHeader():
    channel_id = 0
    sequence_counter = 0
    service_type_identifier = 0

    def add_to_sequence_counter(self):
        self.sequence_counter += 1


class KNXIPHeaderBase():
    header_size=0x06 # KNX Header Frame is 6 Bytes Long
    service_type_identifier = 0x0 #2Byte KNXNETIP_SERVICE_TYPE
    protocol_version = KNXIP_PROTOCOL_VERSION
    total_frame_length = 0 #Total Frame length of the hole KNXIPFrame, should be set by KNX IP Frame Constructor

    def __init__(self,service_type_identifier):
        pass


class KNXIPBodyBase():
    def __init__(self):
        pass


class KNXIPFrame():
    header = KNXIPHeaderBase
    body = KNXIPBodyBase