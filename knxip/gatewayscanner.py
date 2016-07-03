"""

KNX IP Gateway Scanner

Search for an KNX IP Gateway in the network.

Reminder:
This Method is Blocking!

TODO:
    - Implement Return Object for the Device Information we get also from
    the Search Request Response

David Baumann(daBONDi@users.noreply.github.com)
"""

import asyncio
import logging
import struct

from knxip.helper import ip_to_array
from knxip.helper import int_to_array

logger = logging.getLogger(__name__)


class GatewayScanner:

    _default_timeout = 5  # Default Timeout for waiting for a Response
    _default_knx_port = 3671  # Default Port to Broadcast the searchrequest to
    # Default Multicast Address from KNX Assoc "224.0.23.12"
    _default_broadcast_address = "224.0.23.12"

    # Holder for the Transport Protocol Instance of the Broadcast listener
    _listener_transport = None
    # Holder for the Transport Protocol Instance of the Broadcast sender
    _broadcaster_transport = None

    _resolved_gateway_ip_address = None  # Gateway IP Address if found
    _resolved_gateway_ip_port = None  # Gateway Port if found

    _asyncio_loop = None

    def __init__(self, broadcast_source_ip_address="0.0.0.0",
                 broadcast_port=_default_knx_port,
                 broadcast_address=_default_broadcast_address,
                 timeout=_default_timeout):
        """
        Create a new Instance of a GatewayScanner Object

        :param broadcast_source_ip_address: IPv4 Address where we send the
            Search Request out and listen for response
        :param broadcast_port: UDP Port to send the Broadcast
            (Typical KNX IP Port: 3671)
        :param broadcast_address: Broadcast Address to send the
            KNX Searchrequest (Typical "224.0.23.12")
        :param timeout: Time in seconds to wait for an Response before
            returning None on the start_search method
        """
        self.__timeout = timeout
        self._broadcast_ip_address = broadcast_source_ip_address
        self._broadcast_address = broadcast_address
        self._broadcast_port = broadcast_port
        self._timeout = timeout
        pass

    def start_search(self):
        """
        Start the Gateway Search Request and return the address information

        :rtype: (string,int)
        :return: a tuple(string(IP),int(Port) when found or None when
            timeout occurs
        """

        self._asyncio_loop = asyncio.get_event_loop()

        """ Creating Broadcast Receiver """
        coroutine_listen = self._asyncio_loop.create_datagram_endpoint(
            lambda: self.KNXSearchBroadcastReceiverProtocol(
                self._process_response,
                self._timeout_handling,
                self._timeout,
                self._asyncio_loop
            ), local_addr=(self._broadcast_ip_address, 0)
        )
        self._listener_transport, listener_protocol = \
            self._asyncio_loop.run_until_complete(coroutine_listen)

        """ We are ready to fire the broadcast message """
        coroutine_broadcaster = self._asyncio_loop.create_datagram_endpoint(
            lambda: self.KNXSearchBroadcastProtocol(
                        self._asyncio_loop,
                        self._listener_transport.get_extra_info('sockname')
                        [1]),
            remote_addr=(self._broadcast_address, self._broadcast_port))

        self._broadcaster_transport, broadcast_protocol = \
            self._asyncio_loop.run_until_complete(coroutine_broadcaster)
        """ Waiting for all Broadcast receive or timeout """
        self._asyncio_loop.run_forever()

        """ We got Response or Timeout """
        if self._resolved_gateway_ip_address is None and \
           self._resolved_gateway_ip_port is None:
            logger.debug("Gateway not found!")
            return None
        else:
            logger.debug("Gateway found: {}:{}".format(
                self._resolved_gateway_ip_address,
                self._resolved_gateway_ip_port))

            return self._resolved_gateway_ip_address, \
                self._resolved_gateway_ip_port

    def _timeout_handling(self):
        """
        Timeout handler of the Broadcast Listener Socket
        """

        logger.error("Listener don't receive any packets, "
                     "timeout occur(Timeout in Seconds: {} !",
                     format(self._timeout))
        pass

    def _process_response(self, received_data):
        """
        Processing the incoming UDP Datagram from the Broadcast Socket

        :param received_data: UDP Datagram Package to Process
        :type received_data: Byte
        """
        r = bytearray(received_data)
        self._resolved_gateway_ip_address = str.format(
            "{}.{}.{}.{}", r[8], r[9], r[10], r[11])
        self._resolved_gateway_ip_port = struct.unpack(
            '!h', bytes(r[12:14]))[0]
        pass

    class KNXSearchBroadcastReceiverProtocol(asyncio.DatagramProtocol):

        def __init__(self,
                     broadcast_data_received_callback,
                     timeout_callback,
                     timeout_value,
                     loop):
            """
            Create a new KNX Search Broadcast Receiver Protocol Object

            :param broadcast_data_received_callback: function callback
                if data received
            :param timeout_callback: function callback if timeout occur
            :param timeout_value: Timeout in seconds when to stop waiting
            :param loop: Asyncio Loop to use
            """
            self.processing_data = broadcast_data_received_callback
            self.timeout_handler = timeout_callback
            self.timeout_in_seconds = timeout_value
            self.loop = loop
            self.transport = None

            self.h_timeout = asyncio.get_event_loop().call_later(
                self.timeout_in_seconds, self.timeout
            )

        def timeout(self):
            logger.error("Listener don't receive any packets, timeout!")
            self.transport.close()

        def connection_made(self, transport):
            logger.debug("Broadcast Receiver Started")
            self.transport = transport

        def datagram_received(self, data, addr):
            logger.debug(
                "Search Request Response received from {}:{}".
                format(addr[0], addr[1]))
            self.h_timeout.cancel()
            self.processing_data(data)
            self.transport.close()

        def error_received(self, exc):
            if exc:
                logger.error(
                    "Error on the broadcast receiver socket! {}".format(exc))

        def connection_lost(self, exc):
            if exc:
                logger.error(
                    "Error on the broadcast receiver socket! {}".format(exc))
            else:
                logger.debug("Closing broadcast receiver socket")

            self.loop.stop()
            super().connection_lost(exc)

    class KNXSearchBroadcastProtocol:

        def __init__(self, async_loop, listener_port):
            """
             Create a new KNX Search Broadcast Protocol Object

            :param async_loop: Asyncio Base Event Loop to use
            :type async_loop: BaseEventLoop
            """

            self.loop = async_loop
            self.transport = None
            self._listener_port = listener_port

        @staticmethod
        def _build_search_request_data(requestor_ipaddress, requestor_port):
            """
            Build a KNX IP Search Request Broadcast Package

            :param requestor_ipaddress: IP Address of the Search Request
                Response Receiver
            :param requestor_port: Port of the Search Request Response Receiver
            :return: Complete Search Request Broadcast Package
            :rtype: bytes
            """
            req = []
            req.extend([0x06])  # HeaderSize
            req.extend([0x10])  # KNXNetIP Version
            req.extend([0x02, 0x01])  # Search Reques°t
            req.extend([0x00, 0x0E])  # HEADER_SIZE_10 + sizeof(HPAI)
            # ==== Discovery Endpoint HPAI ====
            req.extend([0x08])  # Struct Length
            req.extend([0x01])  # Host Protocol Code = 0x01 = IPV4_UDP
            req.extend(ip_to_array(requestor_ipaddress))
            req.extend(int_to_array(requestor_port))
            return bytes(req)

        def connection_made(self, transport):
            self.transport = transport
            logger.debug("Broadcast Search Request Started")
            self.transport.sendto(
                self._build_search_request_data(
                    self.transport.get_extra_info(
                        'sockname')[0], self._listener_port
                )
            )
            logger.debug(
                "Search Request broadcast send, waiting for response ")

        def error_received(self, exc):
            logger.error("Error on Broadcast Socket")
