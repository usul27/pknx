import asyncio
import socket
import logging
import struct

from knxip.helper import ip_to_array
from knxip.helper import int_to_array

logger = logging.getLogger(__name__)


class gatewayscanner():

    _listener = None
    _broadcaster = None
    _default_timeout = 2 #Static Timeout in Seconds
    _default_knx_port = 3671
    _default_broadcast_address = "224.0.23.11" # Default Multicast Address Reserverd from KNX Assoc "224.0.23.12"

    _listener_transport = None
    _broadcaster_transport = None

    _resolved_gateway_ip_address = None
    _resolved_gateway_ip_port = None

    _asyncio_loop = None

    def __init__(self,broadcast_source_ip_address="0.0.0.0",broadcast_port=_default_knx_port,broadcast_address=_default_broadcast_address,timeout=_default_timeout):
        self.__timeout = timeout
        self._broadcast_ip_address = broadcast_source_ip_address
        self._broadcast_address = broadcast_address
        self._broadcast_port = broadcast_port
        self._timeout = timeout

        logger.debug("Ready To Scan")

    def start_search(self):
        logger.debug("Start Scanning")

        #Get Asyncio Loop
        self._asyncio_loop = asyncio.get_event_loop()


        # Create Receiver Server
        coroutine_listen = self._asyncio_loop.create_datagram_endpoint(
            lambda: self.KNXSearchBroadcastReceiverProtocol(
                self._process_response,
                self._error_handler,
                self._timeout_handling,
                self._timeout
            ), local_addr=(self._broadcast_ip_address,0)
        )
        self._listener_transport, listener_protocol = self._asyncio_loop.run_until_complete(coroutine_listen)  #TODO Timeout with future

        #Building broadcast data message
        broadcast_data = self._build_search_request_data(
            self._get_local_ip(),
            self._listener_transport._sock.getsockname()[1]
        )

        #We are ready to fire the broadcast message
        coroutine_broadcaster = self._asyncio_loop.create_datagram_endpoint(
            lambda: self.KNXSearchBroadcastProtocol(broadcast_data,self._asyncio_loop,self._error_handler), remote_addr=(self._broadcast_address,self._broadcast_port)
        )

        self._broadcaster_transport,broadcast_protocol = self._asyncio_loop.run_until_complete(coroutine_broadcaster)  #TODO: Timeout with future

        #working
        self._asyncio_loop.run_forever()

        print("---------------------------------------------------------------------------------")
        print("Gateway found: {}:{}".format(self._resolved_gateway_ip_address,self._resolved_gateway_ip_port))
        print("---------------------------------------------------------------------------------")

        return self._resolved_gateway_ip_address, self._resolved_gateway_ip_port


    def _timeout_handling(self):
        #TODO: Implement Timeout handling
        logger.error("Listener dont recieve any packets, timeout occure!")
        self._cleanup()
        pass


    def _process_response(self,received_data,received_from):
        self._resolved_gateway_ip_address, self._resolved_gateway_ip_port = self._get_gateway_info_from_response(received_data)
        self._cleanup()
        pass


    def _get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 0))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def _get_gateway_info_from_response(self,response_data):
        r = bytearray(response_data)
        #hpai = r[6:15]
        #iparray = hpai[2:6]
        #ipaddress = str.format("{}.{}.{}.{}", iparray[0], iparray[1], iparray[2], iparray[3])
        #portarray = hpai[6:8]
        #ipaddress = str.format("{}.{}.{}.{}", r[8], r[9], r[10], r[11])
        #port = struct.unpack('!h', bytes(r[12:14]) )[0]

        return str.format("{}.{}.{}.{}", r[8], r[9], r[10], r[11]), struct.unpack('!h', bytes(r[12:14]) )[0]

    def _build_search_request_data(self,requestor_ipaddress,requestor_port):
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

    def _cleanup(self):

        logging.debug("Cleaning up")
        if self._broadcaster_transport is not None:
            self._broadcaster_transport.close()

        if self._listener_transport is not None:
            self._listener_transport.close()

        pass

    def _error_handler(self,oserror):
        self._asyncio_loop.stop()
        #self._cleanup()
        pass

    class KNXSearchBroadcastReceiverProtocol(asyncio.DatagramProtocol):
        def __init__(self,broadcast_data_received_callback,error_handler_callback,timeout_callback,timeout_value):
            self.processing_data = broadcast_data_received_callback
            self.error_handler = error_handler_callback
            self.timeout_handler = timeout_callback
            self.timeout_in_seconds = timeout_value

        def timeout(self):
            self.transport.close()
            self.timeout_handler()

        def connection_made(self,transport):
            logger.debug("Search Request Broadcast Receiver Started")
            self.transport = transport

            self.h_timeout = asyncio.get_event_loop().call_later(
                self.timeout_in_seconds, self.timeout)


        def datagram_received(self, data, addr):
            #self.done = True #TODO: When i do this it hangs, WHY????, we get connection Lost error
            self.h_timeout.cancel()
            self.processing_data(data,addr)
            #self.transport.close()

        def error_received(self,exc):
            logging.error("Error on Listener Socket")
            self.error_handler(exc)

        def connection_lost(self,exc):

            #if exc is not None:
            logging.error("Connection Lost on Listener Socket")
            #self.error_handler(exc) #TODO:: if i uncomment this i get a hang???
            pass


    class KNXSearchBroadcastProtocol:
        def __init__(self,broadcast_data,async_loop,error_handler_callback):
            self.data = broadcast_data
            self.loop = async_loop
            self.transport = None
            self.error_handler = error_handler_callback

        def connection_made(self, transport):
            self.transport = transport
            logging.debug("Broadcast Search Request")
            self.transport.sendto(self.data)

        def error_received(self,exc):
            logging.error("Error on Broadcast Socket")
            self.error_handler(exc)

        def connection_lost(self,exc):
            if exc is not None:
                logging.error("Connection Lost on Broadcast Socket")
                self.error_handler(exc)



if __name__ == '__main__':

    import sys
    logging.basicConfig(level=logging.DEBUG)
    logging.StreamHandler(sys.stdout)


    x = gatewayscanner()
    x.start_search()










