import ipaddress
import struct
from enum import IntEnum

"""Define the Protocol Version for all Factory Classes"""

KNXIP_PROTOCOL_VERSION = 0x10 # Fixed KNX IP Protocol Version in KNXIP V2.1 03.08.01 5.2
KNXIP_HEADER_SIZE = 0x06 # Fixed KNX IP Header defined in KNXIP V2.1 03.08.01 5.2

KNXIP_CONNECTION_REQUEST_TIMOUT = 10
"""KNXNet/IP Client shall wait for 10 seconds for a CONNECT_RESPONSE frame from KNXNet/IP Server"""

KNXIP_CONNECTIONSTATE_REQUEST_TIMEOUT = 10
"""KNXNet/IP Client shall wait for 10 seconds for a CONNECTIONSTATE_RESPONSE frame from KNXNet/IP Server."""

KNXIP_DEVICE_CONFIGURATION_REQUEST_TIMEOUT = 10
"""KNXNet/IP Client shall wait for 10 seconds for a DEVICE_CONFIGURATION_RESPONSE frame from KNXNet/IP Server."""

TUNNELING_REQUEST_TIMEOUT = 1
"""KNXNet/IP Client shall wait for 1 second for a TUNNELING_ACK response on a
TUNNELING_REQUEST frame from KNXNet/IP Server."""


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


class DeviceConfigurationAckCode(IntEnum):
    """Represent a KNXNet/IP Tunnel Ack code defined in KNX Standard v2.1 3.8.1 - 5.5.5"""

    E_NO_ERROR = 0x00
    """The message is received successfully"""

    def __str__(self):
        """Return the DeviceConfigurationAckCode Text as string"""
        if self.value == DeviceConfigurationAckCode.E_NO_ERROR:
            return "The message is received successfully"
        else:
            raise ValueError("Invalid DeviceConfigurationAckCode")


class DescriptionTypeCode(IntEnum):
    """Represent the Description Information Type Code defined in KNX Standard v2.1 3.8.2 - 7.5.4.1"""

    DEVICE_INFO = 0x01
    """Device information e.g. KNX medium."""

    SUPP_SVC_FAMILIES = 0x02
    """Service families supported by the device"""

    IP_CONFIG = 0x03
    """IP configuration"""

    IP_CUR_CONFIG = 0x04
    """current configuration"""

    KNX_ADDRESS = 0x05
    """KNX Addresses"""

    #0x06 to 0xFD reserverd for Future use

    MFR_DATA = 0xFE
    """DIB structure for further data defined by device manufacturer."""

    def __str__(self):
        """Return the Description Type Code Text"""
        if self.value == DescriptionTypeCode.DEVICE_INFO:
            return "Device information e.g. KNX medium."
        elif self.value == DescriptionTypeCode.SUPP_SVC_FAMILIES:
            return "Service families supported by the device"
        elif self.value == DescriptionTypeCode.IP_CONFIG:
            return "IP configuration"
        elif self.value == DescriptionTypeCode.IP_CUR_CONFIG:
            return "current configuration"
        elif self.value == DescriptionTypeCode.KNX_ADDRESS:
            return "KNX Addresses"
        else:
            raise ValueError("Invalid DesciptionTypeCode")


class DescriptionInformationBlockCode(IntEnum):
    """Represent the Description Information Block (DIB) defined in KNX Standard v2.1 3.8.1 - 5.6"""

    DEVICE_INFO = 0x01
    """Device information e.g. KNX medium."""

    SUPP_SVC_FAMILIES = 0x02
    """Service families supported by the device"""

    # 0x03 to 0xFD are Reserved for future use

    MFR_DATA = 0xFE
    """DIB structure for further data defined by device manufacturer"""

    # 0xFF is not Used!

    def __str__(self):
        """Return the Description Information Block Code Information Text"""
        if self.value == DescriptionInformationBlockCode.DEVICE_INFO:
            return "Device information e.g. KNX medium."
        elif self.value == DescriptionInformationBlockCode.SUPP_SVC_FAMILIES:
            return "Service families supported by the device"
        elif self.value == DescriptionInformationBlockCode.MFR_DATA:
            return "DIB structure for further data defined by device manufacturer"
        else:
            raise ValueError("Invalid Description Information Block Code(DIP)")


class KNXMediumCodes(IntEnum):
    """Represent the KNX Medium Codes defined in KNX Standard v2.1 3.8.1- 5.6

    Info:
    These values shall be identical to the encoding of DPT_Media as specified in [01];
    exactly one single bit shall be set.
    """

    # 0x01 is reserved

    KNX_TP = 0x02
    """KNX TP"""

    PL110 = 0x04
    """KNX PL110"""

    # 0x08 is reserved

    RF = 0x10
    """KNX RF"""

    KNXIP = 0x20
    """KNX IP"""


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

    host_protocol_code = HostProtocolCode.IPV4_UDP
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
        Return the Host Protocol Address Information (HPAI) as bytes
        :return: Bytes
        """
        return struct.pack('BB4s2s',
                           self.hpai_frame_default_size,
                           self.host_protocol_code,
                           self.ipv4_address.packed,
                           struct.pack('!H',self.port)
                           )

    @classmethod
    def from_bytes(cls, data):
        """
        Create a new Instance of an Host Protocol Address Information Defined in KNX Standard 3.8.2-8.6.2
        :param bytes: Byte Array of HPAI
        """
        hpai_tuple = struct.unpack('BB4s2s',data)
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


class TunnelKNXLayer(IntEnum):
    """Represent the Tunnel KNX Layers used for the Connection Request Information v2.1 3.8.4 - 4.4.3"""

    TUNNEL_LINKLAYER = 0x02
    """Establish a Data Link Layer tunnel to the KNX network"""

    TUNNEL_RAW = 0x04
    """Establish a raw tunnel to the KNX network"""

    TUNNEL_BUSMONITOR = 0x80
    """Establish a Busmonitor tunnel to the KNX network"""

    def __str__(self):
        """Return the Tunnel KNX Layer Information Text"""
        if self.value == TunnelKNXLayer.TUNNEL_LINKLAYER:
            return "Establish a Data Link Layer tunnel to the KNX network"
        elif self.value == TunnelKNXLayer.TUNNEL_RAW:
            return "Establish a raw tunnel to the KNX network"
        elif self.value == TunnelKNXLayer.TUNNEL_BUSMONITOR:
            return "Establish a Busmonitor tunnel to the KNX network"
        else:
            raise ValueError("Invalid TunnelKNXLayer Value")


class TunnelConnectionRequestInformation():
    """Represent the Tunnel Connection Request Information defined in KNX Standard v2.1 3.8.4 - 4.4.3"""

    __length = 0x04 # Fixed Length
    __tunnel_connection = 0x04 #Fixed Value defined in Standard
    tunnel_knx_layer = 0x02 #Hold the Tunnel KNX Layer Type (Enum TunnelKNXLayer)

    def __init__(self, tunnel_knx_layer=TunnelKNXLayer.TUNNEL_LINKLAYER):
        """ Create a new instance of a TunnelConnectionRequestInformation (CRI) defined in in KNX Standard v2.1 3.8.4 - 4.4.3

        :param tunnel_knx_layer: TunnelKNXLayer
        """
        self.tunnel_knx_layer = tunnel_knx_layer
        pass

    def __bytes__(self):
        """
            Return a Tunnel Connection Request Information (CRI) as bytes

            :return: Bytes
            """
        return struct.pack('BBBB',
                           self.__length,
                           self.__tunnel_connection,
                           self.tunnel_knx_layer,
                           0x0  # Reserved
                           )


class ConnectionTypeSpecificHeader():
    """The connection type specific header items are optional and of variable length depending on the type of the
    connection. Defined in KNX Standard v2.1 3.8.2 - 5.3.1"""

    #TODO: How to Implement this ?? where is the Information, do we need to Pack this into Connectionheader??


class KNXNetIPHeader():
    """Represent the KNXNetIPHeader defined in KNX Standard v2.1 3.8.2 - 2.3.1

    self.total_frame_length need to be Set from the KNXIPFrame Class in the .__bytes__() function
    """

    length = 0x06 # KNX Header Frame is always 6 Bytes Long
    service_type_identifier = 0x00 # ServiceTypeIdentifier Enum
    protocol_version = KNXIP_PROTOCOL_VERSION
    total_frame_length = 0x0006 #HEADER_SIZE_10 + sizeof(Connection Header) + sizeof(cEMI Frame)
    # Total Frame length of the hole KNXIPFrame, should be set by KNX IP Frame Constructor L+12Ocettes???? 3.8.4 5.1??

    def __init__(self, service_type_identifier,total_frame_length=0x0006):
        """
        Create a Instance of an KNXNetIPHeader Object

        :param service_type_identifier: ServiceTypeIdentifier
        """
        self.service_type_identifier = service_type_identifier
        self.total_frame_length=total_frame_length
        pass

    def __bytes__(self):
        """
        Return this KNXNetIPHeader Object as bytes

        :return: bytes
        """
        return struct.pack('BB2s2s',
                           self.length,
                           self.protocol_version,
                           struct.pack('!h',self.service_type_identifier),
                           struct.pack('!h',self.total_frame_length)
                           )

    @classmethod
    def from_bytes(cls, data):
        """
        Construct a KNXNetIPHeader from Binary
        :param data: bytes
        :return: KNXNetIPHeader Instance
        """
        t = struct.unpack('BB2s2s', data)
        return cls(
            ServiceTypeIdentifier(struct.unpack('!h',t[2])[0]),
            struct.unpack('!h',t[3])[0]
        )

    @property
    def total_size(self):
        return self.total_frame_length

    @total_size.setter
    def total_size(self,value):
        self.total_frame_length = value



class KNXNetIPConnectionheader():
    """
    Represent the KNXIP Connection header defined in KNX Standard v2.1 3.8.2 - 5.3
    """

    size = 0x04  # KNX Connection Header Length
    communication_channel_id = 0x0  # Connection channel Id 1 Byte!
    sequence_counter = 0x0  # Sequence Counter need to be set by KNX IP Frame

    def __init__(self,communication_channel_id,sequence_counter):
        """
        Create a Instance of a KNXIP Connection header defined in KNX Standard v2.1 3.8.4 - 4.4.5
        :param communication_channel_id: Integer Id of the communication channel
        :param sequence_counter: Sequence Counter of the communication channel, need to be Upped by KNX Frame on need
        """
        self.communication_channel_id = communication_channel_id
        self.sequence_counter = sequence_counter
        pass

    def __bytes__(self):
        """"
        Return this KNXIPConnectionheader Object as bytes

        :return: bytes
        """

        return struct.pack('BBBB',
                           self.size,
                           self.communication_channel_id,
                           self.sequence_counter,
                           0x0) # Reserved

    @classmethod
    def from_bytes(cls, data):
        """
        Construct a KNXIPConnectionheader from Binary
        :param data: Bytes
        :return: KNXIPConnectionheader
        """
        t = struct.unpack('BBBB', data)
        return cls(
            t[1],
            t[2]
        )


class KNXNetIPBody():
    """
    Represent the KNXNet IP Body defined in KNX Standard v2.1 3.8.4 - 4.4.6
    """
    knxip_connection_header = None
    knxip_cemi_frame = None

    has_knxip_cemi_frame = False

    def __init__(self, knxip_connection_header, knxip_cemi_frame=None):
        self.knxip_connection_header = knxip_connection_header
        if knxip_cemi_frame is not None:
            self.knxip_cemi_frame = knxip_cemi_frame
            self.has_knxip_cemi_frame = True

    def __bytes__(self):
        if self.has_knxip_cemi_frame:
            raise NotImplementedError
            #TODO: Implement with CEMI Frame
        else:
            return bytes(self.knxip_connection_header)

    @classmethod
    def from_bytes(cls,data):
        """
        Create a instance of a KNXNetIPBody defined in KNX Standard v2.1 3.8.4 - 4.4.6
        :param data: bytes
        :return: KNXNetIPBody
        """
        if len(data) > 4:
            # TODO: Implement CEMI Frame
            raise NotImplementedError
        else:
            # No Data only connection header
            return cls(KNXNetIPConnectionheader.from_bytes(data))





class KNXNetIPFrame():

    knxip_header = None
    knxip_body = None

    def __init__(self,knxip_header,knxip_body=0x0):
        self.knxip_header = knxip_header
        self.knxip_body = knxip_body
        pass

    def __bytes__(self):
        self.knxip_header.total_size = len(bytes(self.knxip_header) + bytes(self.knxip_body))
        return bytes(self.knxip_header) + bytes(self.knxip_body)

    @classmethod
    def from_bytes(cls, data):
        return



class CEMIFrame():

    def __init__(self):
        raise NotImplementedError
