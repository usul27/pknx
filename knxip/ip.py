"""Module to connect to a KNX bus using a KNX/IP tunnelling interface.
"""
import socket
import threading
import logging
import queue as queue
import socketserver as SocketServer

from knxip.core import KNXException, ValueCache, E_NO_ERROR
from knxip.helper import int_to_array, ip_to_array
from knxip.gatewayscanner import GatewayScanner


class KNXIPFrame():
    """Representation of a KNX/IP frame."""

    SEARCH_REQUEST = 0x0201
    SEARCH_RESPONSE = 0x0202
    DESCRIPTION_REQUEST = 0x0203
    DESCRIPTION_RESPONSE = 0x0204
    CONNECT_REQUEST = 0x0205
    CONNECT_RESPONSE = 0x0206
    CONNECTIONSTATE_REQUEST = 0x0207
    CONNECTIONSTATE_RESPONSE = 0x0208
    DISCONNECT_REQUEST = 0x0209
    DISCONNECT_RESPONSE = 0x020a
    DEVICE_CONFIGURATION_REQUEST = 0x0310
    DEVICE_CONFIGURATION_ACK = 0x0111
    TUNNELING_REQUEST = 0x0420
    TUNNELLING_ACK = 0x0421
    ROUTING_INDICATION = 0x0530
    ROUTING_LOST_MESSAGE = 0x0531

    DEVICE_MGMT_CONNECTION = 0x03
    TUNNEL_CONNECTION = 0x04
    REMLOG_CONNECTION = 0x06
    REMCONF_CONNECTION = 0x07
    OBJSVR_CONNECTION = 0x08

    body = None

    def __init__(self, service_type_id):
        """Initalize an empty frame with the given service type."""
        self.service_type_id = service_type_id

    def to_frame(self):
        """Return the frame as an array of bytes."""
        return bytearray(self.header() + self.body)

    @classmethod
    def from_frame(cls, frame):
        """Initilize the frame object based on a KNX/IP data frame."""
        # TODO: Check length
        p = cls(frame[2] * 256 + frame[3])
        p.body = frame[6:]
        return p

    def total_length(self):
        """Return the length of the frame (in bytes)."""
        return 6 + len(self.body)

    def header(self):
        """Return the frame header (as an array of bytes)."""
        tl = self.total_length()
        res = [0x06, 0x10, 0, 0, 0, 0]
        res[2] = (self.service_type_id >> 8) & 0xff
        res[3] = (self.service_type_id >> 0) & 0xff
        res[4] = (tl >> 8) & 0xff
        res[5] = (tl >> 0) & 0xff
        return res


class KNXTunnelingRequest:
    """Representation of a KNX/IP tunnelling request."""

    seq = 0
    cEmi = None
    channel = 0

    def __init__(self):
        """Initialize object."""
        pass

    @classmethod
    def from_body(cls, body):
        """Create a tunnelling request from a given body of a KNX/IP frame."""
        # TODO: Check length
        p = cls()
        p.channel = body[1]
        p.seq = body[2]
        p.cEmi = body[4:]
        return p


class CEMIMessage():
    """Representation of a CEMI message."""

    CMD_GROUP_READ = 1
    CMD_GROUP_WRITE = 2
    CMD_GROUP_RESPONSE = 3
    CMD_UNKNOWN = 0xff

    code = 0
    ctl1 = 0
    ctl2 = 0
    src_addr = None
    dst_addr = None
    cmd = None
    tpci_apci = 0
    mpdu_len = 0
    data = [0]

    def __init__(self):
        """Initialize object."""
        pass

    @classmethod
    def from_body(cls, cemi):
        """Create a new CEMIMessage initialized from the given CEMI data."""
        # TODO: check that length matches
        m = cls()
        m.code = cemi[0]
        offset = cemi[1]

        m.ctl1 = cemi[2 + offset]
        m.ctl2 = cemi[3 + offset]

        m.src_addr = cemi[4 + offset] * 256 + cemi[5 + offset]
        m.dst_addr = cemi[6 + offset] * 256 + cemi[7 + offset]

        m.mpdu_len = cemi[8 + offset]

        tpci_apci = cemi[9 + offset] * 256 + cemi[10 + offset]
        apci = tpci_apci & 0x3ff

        # for APCI codes see KNX Standard 03/03/07 Application layer
        # table Application Layer control field
        if (apci & 0x080):
            # Group write
            m.cmd = CEMIMessage.CMD_GROUP_WRITE
        elif (apci == 0):
            m.cmd = CEMIMessage.CMD_GROUP_READ
        elif (apci & 0x40):
            m.cmd = CEMIMessage.CMD_GROUP_RESPONSE
        else:
            m.cmd = CEMIMessage.CMD_NOT_IMPLEMENTED

        apdu = cemi[10 + offset:]
        if len(apdu) != m.mpdu_len:
            raise KNXException(
                "APDU LEN should be {} but is {}".format(
                    m.mpdu_len, len(apdu)))

        if len(apdu) == 1:
            m.data = [apci & 0x2f]
        else:
            m.data = cemi[11 + offset:]

        return m

    def init_group(self, dst_addr=1):
        """Initilize the CEMI frame with the given destination address."""
        self.code = 0x11
        # frametype 1, repeat 1, system broadcast 1, priority 3, ack-req 0,
        # confirm-flag 0
        self.ctl1 = 0xbc
        self.ctl2 = 0xe0  # dst addr type 1, hop count 6, extended frame format
        self.src_addr = 0
        self.dst_addr = dst_addr

    def init_group_write(self, dst_addr=1, data=[0]):
        """Initialize the CEMI frame for a group write operation."""
        self.init_group(dst_addr)

        # unnumbered data packet, group write
        self.tpci_apci = 0x00 * 256 + 0x80

        self.data = data

    def init_group_read(self, dst_addr=1):
        """Initialize the CEMI frame for a group read operation."""
        self.init_group(dst_addr)
        self.tpci_apci = 0x00  # unnumbered data packet, group read
        self.data = [0]

    def to_body(self):
        """Convert the CEMI frame object to its byte representation."""
        b = [self.code, 0x00, self.ctl1, self.ctl2,
             (self.src_addr >> 8) & 0xff, (self.src_addr >> 0) & 0xff,
             (self.dst_addr >> 8) & 0xff, (self.dst_addr >> 0) & 0xff,
             ]
        if (len(self.data) == 1) and ((self.data[0] & 3) == self.data[0]):
            # less than 6 bit of data, pack into APCI byte
            b.extend([1, (self.tpci_apci >> 8) & 0xff,
                      ((self.tpci_apci >> 0) & 0xff) + self.data[0]])
        else:
            b.extend([1 + len(self.data), (self.tpci_apci >> 8) &
                      0xff, (self.tpci_apci >> 0) & 0xff])
            b.extend(self.data)

        return b

    def __str__(self):
        """Return a human readable string for debugging."""
        c = "??"
        if self.cmd == self.CMD_GROUP_READ:
            c = "RD"
        elif self.cmd == self.CMD_GROUP_WRITE:
            c = "WR"
        elif self.cmd == self.CMD_GROUP_RESPONSE:
            c = "RS"
        return "{0:x}->{1:x} {2} {3}".format(
            self.src_addr, self.dst_addr, c, self.data)


class KNXIPTunnel():
    """A connection to a KNX/IP tunnelling interface."""

    data_server = None
    control_socket = None
    channel = None
    seq = 0
    valueCache = None
    data_handler = None
    result_queue = None
    notify = None
    address_listeners = {}

    def __init__(self, ip, port=3671, valueCache=None):
        """Initialize the connection to the given host/port

        Initialized the connection, but does not connect.
        """
        self.remote_ip = ip
        self.remote_port = port
        self.discovery_port = None
        self.data_port = None
        self.connected = False
        self.result_queue = queue.Queue()
        self.unack_queue = queue.Queue()
        if valueCache is None:
            self.valueCache = ValueCache()
        else:
            self.valueCache = ValueCache

    def __del__(self):
        """Make sure an open tunnel connection will be closed"""
        self.disconnect()

    def connect(self, timeout=2):
        """Connect to the KNX/IP tunnelling interface.

        If the remote address is "0.0.0.0", it will use the Gateway scanner
        to automatically detect a KNX gateway and it will connect to it if one
        has been found.

        Returns true if a connection could be established, false otherwise
        """

        if self.connected:
            logging.info("KNXIPTunnel connect request ignored, "
                         "already connected")
            return True

        if (self.remote_ip == "0.0.0.0"):
            scanner = GatewayScanner()
            try:
                ip, port = scanner.start_search()
                logging.info("Found KNX gateway {}/{}".format(ip, port))
                self.remote_ip = ip
                self.remote_port = port
            except:
                logging.error("No KNX/IP gateway given and no gateway "
                              "found by scanner, aborting")

        # Find my own IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.remote_ip, self.remote_port))
        local_ip = s.getsockname()[0]

        if self.data_server:
            logging.info("Data server already running, not starting again")
        else:
            self.data_server = DataServer((local_ip, 0), DataRequestHandler)
            self.data_server.tunnel = self
            _ip, self.data_port = self.data_server.server_address
            data_server_thread = threading.Thread(
                target=self.data_server.serve_forever)
            data_server_thread.daemon = True
            data_server_thread.start()
            logging.debug(
                "Started data server on UDP port {}".format(self.data_port))

        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.control_socket.bind((local_ip, 0))
        self.control_socket.settimeout(timeout)

        # Connect packet
        p = []
        p.extend([0x06, 0x10])  # header size, protocol version
        p.extend(int_to_array(KNXIPFrame.CONNECT_REQUEST, 2))
        p.extend([0x00, 0x1a])  # total length = 24 octet

        # Control endpoint
        p.extend([0x08, 0x01])  # length 8 bytes, UPD
        _ip, port = self.control_socket.getsockname()
        p.extend(ip_to_array(local_ip))
        p.extend(int_to_array(port, 2))

        # Data endpoint
        p.extend([0x08, 0x01])  # length 8 bytes, UPD
        p.extend(ip_to_array(local_ip))
        p.extend(int_to_array(self.data_port, 2))

        #
        p.extend([0x04, 0x04, 0x02, 0x00])

        try:
            self.control_socket.sendto(bytes(p),
                                       (self.remote_ip, self.remote_port))
            received = self.control_socket.recv(1024)
        except socket.error:
            self.control_socket = None
            logging.error("KNX/IP gateway did not responde on connect request")
            return False

        # Check if the response is an TUNNELING ACK
        r_sid = received[2] * 256 + received[3]

        if r_sid == KNXIPFrame.CONNECT_RESPONSE:
            self.channel = received[6]
            status = received[7]
            if (status == 0):
                self.hpai = received[8:10]
                logging.debug("Connected KNX IP tunnel " +
                              "(Channel: {}, HPAI: {} {})".format(
                                  self.channel, self.hpai[0], self.hpai[1]))
            else:
                logging.error("KNX IP tunnel connect error:" +
                              "(Channel: {}, Status: {})".format(
                                  self.channel, status))
                return False

        else:
            logging.error("Could not initiate tunnel connection, STI = {0:x}"
                          .format(r_sid))
            return False

        self.connected = True
        return True

    def disconnect(self):
        """Disconnect an open tunnel connection"""
        if self.channel:
            logging.debug("Disconnecting KNX/IP tunnel...")

            b = []
            # =========== IP Header ==========
            b.extend([0x06])  # HeaderSize
            b.extend([0x10])  # KNXIP Protocl Version
            b.extend([0x02, 0x09])  # Service Identifier = Disconnect Request
            # Headersize +2 + sizeof(HPAI) = 2 (Headersize) + 2
            # + 8(sizeof(HPAI) = 16 = 0x10 || Need to be 2 Bytes
            b.extend([0x00, 0x10])

            # ============ IP Body ==========
            b.extend([self.channel])  # Communication Channel Id
            b.extend([0x00])  # Reserverd
            # =========== Client HPAI ===========
            b.extend([0x08])  # HPAI Length
            b.extend([0x01])  # Host Protocol
            # Tunnel Client Socket IP
            b.extend(ip_to_array(self.control_socket.getsockname()[0]))
            # Tunnel Client Socket Port
            b.extend(int_to_array(self.control_socket.getsockname()[1]))

            # TODO: Glaube Sequence erhöhen ist nicht notwendig im Control
            # Tunnel beim Disconnect???
            if (self.seq < 0xff):
                self.seq += 1
            else:
                self.seq = 0

            self.control_socket.sendto(
                bytes(b), (self.remote_ip, self.remote_port))
            # TODO: Impelement the Disconnect_Response Handling from Gateway
            # Control Channel > Client Control Channel

        else:
            logging.debug("Disconnect - no connection, nothing to do")

        self.connected = False

    def send_tunnelling_request(self, cemi):
        """Send a tunneling request based on the given CEMI data.

        This method does not wait for an acknowledge or result frame.
        """
        if self.data_server is None:
            raise KNXException("KNX tunnel not connected")

        f = KNXIPFrame(KNXIPFrame.TUNNELING_REQUEST)
        # Connection header see KNXnet/IP 4.4.6 TUNNELLING_REQUEST
        b = [0x04, self.channel, self.seq, 0x00]
        if (self.seq < 0xff):
            self.seq += 1
        else:
            self.seq = 0
        b.extend(cemi.to_body())
        f.body = b
        self.data_server.socket.sendto(
            f.to_frame(), (self.remote_ip, self.remote_port))
        # TODO: wait for ack

    def group_read(self, addr, use_cache=True, timeout=2):
        """Send a group read to the KNX bus and return the result."""
        if use_cache:
            res = self.valueCache.get(addr)
            if res:
                logging.debug(
                    "Got value of group address {} from cache: {}".format(
                        addr, res))
                return res

        cemi = CEMIMessage()
        cemi.init_group_read(addr)
        # There might be old messages in the result quue, remove them
        self.result_queue.queue.clear()
        self.send_tunnelling_request(cemi)
        # Wait for the result
        try:
            res = self.result_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            # TODO: cleanup
            return None

        self.result_queue.task_done()
        return res

    def group_write(self, addr, data):
        """Send a group write to the given address.

        The method does not check if the address exists and the write request
        is valid.
        """
        cemi = CEMIMessage()
        cemi.init_group_write(addr, data)
        self.send_tunnelling_request(cemi)

    def group_toggle(self, addr, use_cache=True):
        """Toggle the value of an 1-bit group address.

        If the object has a value != 0, it will be set to 0, otherwise to 1
        """
        d = self.group_read(addr, use_cache)
        if len(d) != 1:
            problem = "Can't toggle a {}-octet group address {}".format(
                len(d), addr)
            logging.error(problem)
            raise KNXException(problem)

        if (d[0] == 0):
            self.group_write(addr, [1])
        elif (d[0] == 1):
            self.group_write(addr, [0])
        else:
            problem = "Can't toggle group address {} as value is {}".format(
                addr, d[0])
            logging.error(problem)
            raise KNXException(problem)

    def register_listener(self, address, func):
        """Adds a listener to messages received on a specific address

        If some KNX messages will be received from the KNX bus, this listener
        will be called func(address, data).
        There can be multiple listeners for a given address
        """
        try:
            listeners = self.address_listeners[address]
        except KeyError:
            listeners = []
            self.address_listeners[address] = listeners

        if not(func in listeners):
            listeners.append(func)

        return True

    def unregister_listener(self, address, func):
        """Removes a listener function for a given address

        Remove the listener for the given address. Returns true if the listener
        was found and removed, false otherwise
        """
        listeners = self.address_listeners[address]
        if listeners is None:
            return False

        if func in listeners:
            listeners.remove(func)
            return True

        return False

    def received_message(self, address, data):
        """Process a message received from the KNX bus."""
        self.valueCache.set(address, data)
        if self.notify:
            self.notify(address, data)

        try:
            listeners = self.address_listeners[address]
        except KeyError:
            listeners = None

        for listener in listeners:
            listener(address, data)


class DataRequestHandler(SocketServer.BaseRequestHandler):
    """The class that handles incoming UDP packets from the KNX/IP tunnel."""

    def handle(self):
        """Process an incoming package."""
        data = self.request[0]
        socket = self.request[1]

        f = KNXIPFrame.from_frame(data)

        if f.service_type_id == KNXIPFrame.TUNNELING_REQUEST:
            req = KNXTunnelingRequest.from_body(f.body)
            msg = CEMIMessage.from_body(req.cEmi)
            send_ack = False

            # print(msg)
            tunnel = self.server.tunnel

            if msg.code == 0x29:
                # LData.req
                send_ack = True
            elif msg.code == 0x2e:
                # LData.con
                send_ack = True
            else:
                problem = "Unimplemented cEMI message code {}".format(msg.code)
                logging.error(problem)
                raise KNXException(problem)

            # Cache data
            if (msg.cmd == CEMIMessage.CMD_GROUP_WRITE) or (
                    msg.cmd == CEMIMessage.CMD_GROUP_RESPONSE):
                    # saw a value for a group address on the bus
                tunnel.received_message(msg.dst_addr, msg.data)

            # Put RESPONSES into the result queue
            if (msg.cmd == CEMIMessage.CMD_GROUP_RESPONSE):
                tunnel.result_queue.put(msg.data)

            if send_ack:
                bodyack = [0x04, req.channel, req.seq, E_NO_ERROR]
                ack = KNXIPFrame(KNXIPFrame.TUNNELLING_ACK)
                ack.body = bodyack
                socket.sendto(ack.to_frame(), self.client_address)

        elif f.service_type_id == KNXIPFrame.TUNNELLING_ACK:
            logging.debug("Received tunneling ACK")
        elif f.service_type_id == KNXIPFrame.DISCONNECT_RESPONSE:
            logging.debug("Disconnected")
            self.channel = None
            tunnel = self.server.tunnel
            tunnel.data_server.shutdown()
            tunnel.data_server = None
        else:
            logging.info("Message type {} not yet implemented".format(
                         f.service_type_id))


class DataServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    """Server that handled the UDP connection to the KNX/IP tunnel."""

    pass
