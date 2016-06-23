
from knxip.helper import ip_to_array
from knxip.helper import int_to_array
from knxip.helper import bytes_to_str

import asyncio
import socket
import struct
try:
    import signal
except ImportError:
    signal = None

def get_ip():
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

print(get_ip())

def searchrequestdone(data):
    print("handler (0)",data)

    r = bytearray(data)
    hpai = r[6:15]
    iparray = hpai[2:6]
    ipaddress = str.format("{}.{}.{}.{}", iparray[0],iparray[1],iparray[2],iparray[3])
    portarray = hpai[6:8]
    broadcast_transport.close()
    listen_transport.close()
    print("---------------------------------------------------------------------------------")
    print("Gateway found: {}:{}".format(ipaddress,struct.unpack('!h',bytes(portarray))[0]))
    print("---------------------------------------------------------------------------------")


class ReceiverProtocol:
    def __init__(self,handler):
        self.handler = handler
    def connection_made(self, transport):
        print('Listener started', transport)
        self.transport = transport

    def datagram_received(self, data, addr):
        print('Listener received:', data, addr)
        self.handler(data)
        self.transport.close()
        #self.transport.sendto(data, addr)

    def error_received(self, exc):
        print('Listener Error received:')

    def connection_lost(self, exc):
        print('Listener Stopped')

class SenderProtocol:

    def __init__(self,data,loop):
        self.data = data
        self.loop = loop
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('Broadcaster sending "{}"'.format(self.data))
        self.transport.sendto(self.data)

        #print('waiting to receive')

    def datagram_received(self, data, addr):
        print('Broadcaster received "{}"'.format(data.decode()))
        self.transport.close()

    def error_received(self, exc):
        print('Broadcaster received:', exc)

    def connection_lost(self, exc):
        print('Broadcaster closing transport')
        loop = asyncio.get_event_loop()
        loop.stop()

multicastgroup = "224.0.23.12"

loop = asyncio.get_event_loop()
#loop.add_signal_handler(signal.SIGINT,loop.stop())

host=get_ip()

default_knx_port=3671

listen = loop.create_datagram_endpoint(
    lambda: ReceiverProtocol(searchrequestdone), local_addr=("0.0.0.0",0)
)
listen_transport, listen_protocol = loop.run_until_complete(listen)

port = listen_transport._sock.getsockname()[1]

#Send Package
req = []
req.extend([0x06])  # HeaderSize
req.extend([0x10])  # KNXNetIP Version
req.extend([0x02, 0x01])  # Search Request
req.extend([0x00, 0x0E])  # HEADER_SIZE_10 + sizeof(HPAI)
# ==== Discovery Endpoint HPAI ====
req.extend([0x08])  # Struct Length
req.extend([0x01])  # Host Protocol Code = 0x01 = IPV4_UDP
req.extend(ip_to_array(host))
req.extend(int_to_array(port))

broadcast = loop.create_datagram_endpoint(
    lambda: SenderProtocol(bytes(req),loop),remote_addr=(multicastgroup,default_knx_port)
)

broadcast_transport,broadcast_protocol = loop.run_until_complete(broadcast)


try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
listen_transport.close()
loop.close()



