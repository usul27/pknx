"""Module to connect to a KNX bus using a KNX/IP tunnelling interface.
"""
import socket
import threading
import logging
import time
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

    # CONNECTIONSTATE_RESPONSE Status Codes
    # 3.8.2 - 7.8.4
    E_DATA_CONNECTION = 0x26
    E_CONNECTION_ID = 0x21
    E_KNX_CONNECTION = 0x27

    # Generic Response Status Code
    E_NO_ERROR = 0x0

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
        ipframe = cls(frame[2] * 256 + frame[3])
        ipframe.body = frame[6:]
        return ipframe

    def total_length(self):
        """Return the length of the frame (in bytes)."""
        return 6 + len(self.body)

    def header(self):
        """Return the frame header (as an array of bytes)."""
        total_length = self.total_length()
        res = [0x06, 0x10, 0, 0, 0, 0]
        res[2] = (self.service_type_id >> 8) & 0xff
        res[3] = (self.service_type_id >> 0) & 0xff
        res[4] = (total_length >> 8) & 0xff
        res[5] = (total_length >> 0) & 0xff
        return res


# pylint: disable=too-few-public-methods
class KNXTunnelingRequest:
    """Representation of a KNX/IP tunnelling request."""

    def __init__(self):
        """Initialize object."""
        self.seq = 0
        self.cemi = None
        self.channel = 0

    @classmethod
    def from_body(cls, body):
        """Create a tunnelling request from a given body of a KNX/IP frame."""
        # TODO: Check length
        request = cls()
        request.channel = body[1]
        request.seq = body[2]
        request.cemi = body[4:]
        return request


# pylint: disable=too-many-instance-attributes
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
        message = cls()
        message.code = cemi[0]
        offset = cemi[1]

        message.ctl1 = cemi[2 + offset]
        message.ctl2 = cemi[3 + offset]

        message.src_addr = cemi[4 + offset] * 256 + cemi[5 + offset]
        message.dst_addr = cemi[6 + offset] * 256 + cemi[7 + offset]

        message.mpdu_len = cemi[8 + offset]

        tpci_apci = cemi[9 + offset] * 256 + cemi[10 + offset]
        apci = tpci_apci & 0x3ff

        # for APCI codes see KNX Standard 03/03/07 Application layer
        # table Application Layer control field
        if apci & 0x080:
            # Group write
            message.cmd = CEMIMessage.CMD_GROUP_WRITE
        elif apci == 0:
            message.cmd = CEMIMessage.CMD_GROUP_READ
        elif apci & 0x40:
            message.cmd = CEMIMessage.CMD_GROUP_RESPONSE
        else:
            message.cmd = CEMIMessage.CMD_UNKNOWN

        apdu = cemi[10 + offset:]
        if len(apdu) != message.mpdu_len:
            raise KNXException(
                "APDU LEN should be {} but is {}".format(
                    message.mpdu_len, len(apdu)))

        if len(apdu) == 1:
            message.data = [apci & 0x2f]
        else:
            message.data = cemi[11 + offset:]

        return message

    def init_group(self, dst_addr=1):
        """Initilize the CEMI frame with the given destination address."""
        self.code = 0x11
        # frametype 1, repeat 1, system broadcast 1, priority 3, ack-req 0,
        # confirm-flag 0
        self.ctl1 = 0xbc
        self.ctl2 = 0xe0  # dst addr type 1, hop count 6, extended frame format
        self.src_addr = 0
        self.dst_addr = dst_addr

    def init_group_write(self, dst_addr=1, data=None):
        """Initialize the CEMI frame for a group write operation."""
        self.init_group(dst_addr)

        # unnumbered data packet, group write
        self.tpci_apci = 0x00 * 256 + 0x80

        if data is None:
            self.data = [0]
        else:
            self.data = data

    def init_group_read(self, dst_addr=1):
        """Initialize the CEMI frame for a group read operation."""
        self.init_group(dst_addr)
        self.tpci_apci = 0x00  # unnumbered data packet, group read
        self.data = [0]

    def to_body(self):
        """Convert the CEMI frame object to its byte representation."""
        body = [self.code, 0x00, self.ctl1, self.ctl2,
                (self.src_addr >> 8) & 0xff, (self.src_addr >> 0) & 0xff,
                (self.dst_addr >> 8) & 0xff, (self.dst_addr >> 0) & 0xff,
               ]
        if (len(self.data) == 1) and ((self.data[0] & 3) == self.data[0]):
            # less than 6 bit of data, pack into APCI byte
            body.extend([1, (self.tpci_apci >> 8) & 0xff,
                         ((self.tpci_apci >> 0) & 0xff) + self.data[0]])
        else:
            body.extend([1 + len(self.data), (self.tpci_apci >> 8) &
                         0xff, (self.tpci_apci >> 0) & 0xff])
            body.extend(self.data)

        return body

    def __str__(self):
        """Return a human readable string for debugging."""
        cmd = "??"
        if self.cmd == self.CMD_GROUP_READ:
            cmd = "RD"
        elif self.cmd == self.CMD_GROUP_WRITE:
            cmd = "WR"
        elif self.cmd == self.CMD_GROUP_RESPONSE:
            cmd = "RS"
        return "{0:x}->{1:x} {2} {3}".format(
            self.src_addr, self.dst_addr, cmd, self.data)


class KNXIPTunnel():
    """A connection to a KNX/IP tunnelling interface."""

    data_server = None
    control_socket = None
    channel = None
    seq = 0
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
        self.ack_semaphore = threading.Semaphore(0)
        self.conn_state_ack_semaphore = threading.Semaphore(0)
        if valueCache is None:
            self.value_cache = ValueCache()
        else:
            self.value_cache = valueCache
        self.connection_state = 0
        self.keepalive_thread = threading.Thread(target=self.keepalive,
                                                 args=())
        self.keepalive_thread.daemon = True
        self.keepalive_thread.start()

    def __del__(self):
        """Make sure an open tunnel connection will be closed"""
        self.disconnect()

    def keepalive(self):
        """Background method that makes sure the connection is still open."""
        while True:
            if self.connected:
                self.check_connection_state()
            time.sleep(60)

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

        if self.remote_ip == "0.0.0.0":
            scanner = GatewayScanner()
            try:
                ipaddr, port = scanner.start_search()
                logging.info("Found KNX gateway %s/%s", ipaddr, port)
                self.remote_ip = ipaddr
                self.remote_port = port
            except TypeError:
                logging.error("No KNX/IP gateway given and no gateway "
                              "found by scanner, aborting %s")

        # Clean up cache
        self.value_cache.clear()

        # Find my own IP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((self.remote_ip, self.remote_port))
        local_ip = sock.getsockname()[0]

        if self.data_server:
            logging.info("Data server already running, not starting again")
        else:
            self.data_server = DataServer((local_ip, 0),
                                          DataRequestHandler,
                                          self)
            dummy_ip, self.data_port = self.data_server.server_address
            data_server_thread = threading.Thread(
                target=self.data_server.serve_forever)
            data_server_thread.daemon = True
            data_server_thread.start()
            logging.debug(
                "Started data server on UDP port %s", self.data_port)

        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.control_socket.bind((local_ip, 0))
        self.control_socket.settimeout(timeout)

        # Connect packet
        frame = KNXIPFrame(KNXIPFrame.CONNECT_REQUEST)

        # Control endpoint
        body = []
        body.extend([0x08, 0x01])  # length 8 bytes, UPD
        dummy_ip, port = self.control_socket.getsockname()
        body.extend(ip_to_array(local_ip))
        body.extend(int_to_array(port, 2))

        # Data endpoint
        body.extend([0x08, 0x01])  # length 8 bytes, UPD
        body.extend(ip_to_array(local_ip))
        body.extend(int_to_array(self.data_port, 2))

        #
        body.extend([0x04, 0x04, 0x02, 0x00])
        frame.body = body

        try:
            self.control_socket.sendto(bytes(frame.to_frame()),
                                       (self.remote_ip, self.remote_port))
            received = self.control_socket.recv(1024)
        except socket.error:
            self.control_socket = None
            logging.error("KNX/IP gateway did not respond to connect request")
            return False

        # Check if the response is an TUNNELING ACK
        r_sid = received[2] * 256 + received[3]

        if r_sid == KNXIPFrame.CONNECT_RESPONSE:
            self.channel = received[6]
            status = received[7]
            if status == 0:
                hpai = received[8:10]
                logging.debug("Connected KNX IP tunnel " +
                              "(Channel: {}, HPAI: {} {})".format(
                                  self.channel, hpai[0], hpai[1]))
            else:
                logging.error("KNX IP tunnel connect error:" +
                              "(Channel: {}, Status: {})".format(
                                  self.channel, status))
                return False

        else:
            logging.error(
                "Could not initiate tunnel connection, STI = {0:%s}", r_sid)
            return False

        self.connected = True

        return True

    def disconnect(self):
        """Disconnect an open tunnel connection"""
        if self.channel:
            logging.debug("Disconnecting KNX/IP tunnel...")

            frame = KNXIPFrame(KNXIPFrame.DISCONNECT_REQUEST)
            frame.body = self.hpai_body()

            # TODO: Glaube Sequence erhöhen ist nicht notwendig im Control
            # Tunnel beim Disconnect???
            if self.seq < 0xff:
                self.seq += 1
            else:
                self.seq = 0

            self.control_socket.sendto(
                bytes(frame.to_frame()), (self.remote_ip, self.remote_port))
            # TODO: Impelement the Disconnect_Response Handling from Gateway
            # Control Channel > Client Control Channel

        else:
            logging.debug("Disconnect - no connection, nothing to do")

        self.connected = False

    def check_connection_state(self):
        """Check the state of the connection using connection state request.

        This sends a CONNECTION_STATE_REQUEST. This method will only return
        True, if the connection is established and no error code is returned
        from the KNX/IP gateway
        """
        if not self.connected:
            self.connection_state = -1
            return False

        frame = KNXIPFrame(KNXIPFrame.CONNECTIONSTATE_REQUEST)
        frame.body = self.hpai_body()

        # Send maximum 3 connection state requests with a 10 second timeout
        res = False
        self.connection_state = 0

        maximum_retry = 3
        for retry_counter in range(0, maximum_retry):
            logging.debug("Heartbeat: Send connection state request")

            # Suggestion:
            # Carve the Control Socket out of the KNXIPTunnel
            # Class and Public only the Send and Receive
            # function and Implement in there the Heartbeat so we
            # can block when other Functions want to send
            self.control_socket.settimeout(10)  # Kind of a quirks
            self.control_socket.sendto(bytes(frame.to_frame()),
                                       (self.remote_ip, self.remote_port))

            try:
                self.control_socket.sendto(bytes(frame.to_frame()),
                                           (self.remote_ip, self.remote_port))
                receive = self.control_socket.recv(1024)

            except socket.timeout:
                logging.info("Heartbeat: No response, Retry Counter %d/%d",
                             retry_counter, maximum_retry)
                break

            frame = KNXIPFrame.from_frame(receive)
            if frame.service_type_id == KNXIPFrame.CONNECTIONSTATE_RESPONSE:
                if frame.body[1] == KNXIPFrame.E_NO_ERROR:
                    logging.debug("Heartbeat: Successful")
                    res = True
                    break
                if frame.body[1] == KNXIPFrame.E_CONNECTION_ID:
                    logging.error(
                        "Heartbeat: Response No active "\
                        "connection found for Channel:%d ", self.channel
                    )
                if frame.body[1] == KNXIPFrame.E_DATA_CONNECTION:
                    logging.error(
                        "Heartbeat: Response Data Connection Error Response "\
                        "for  Channel:%d ", self.channel
                    )
                if frame.body[1] == KNXIPFrame.E_DATA_CONNECTION:
                    logging.error(
                        "Heartbeat: Response KNX Sub Network Error Response "\
                        "for  Channel:%d ", self.channel
                    )
            else:
                logging.error("Heartbeat: Invalid Response!")

        if self.connection_state != 0:
            logging.info("Heartbeat: Connection state was %s",
                         self.connection_state)
            res = False

        if not res:
            if self.connection_state == 0:
                self.connection_state = -1
            self.disconnect()
            return False

        return True

    def hpai_body(self):
        """ Create a body with HPAI information.

        This is used for disconnect and connection state requests.
        """
        body = []
        # ============ IP Body ==========
        body.extend([self.channel])  # Communication Channel Id
        body.extend([0x00])  # Reserverd
        # =========== Client HPAI ===========
        body.extend([0x08])  # HPAI Length
        body.extend([0x01])  # Host Protocol
        # Tunnel Client Socket IP
        body.extend(ip_to_array(self.control_socket.getsockname()[0]))
        # Tunnel Client Socket Port
        body.extend(int_to_array(self.control_socket.getsockname()[1]))

        return body

    def send_tunnelling_request(self, cemi, auto_connect=True):
        """Sends a tunneling request based on the given CEMI data.

        This method does not wait for an acknowledge or result frame.
        """
        if self.data_server is None:
            if auto_connect:
                self.connect()
            else:
                raise KNXException("KNX tunnel not connected")

        frame = KNXIPFrame(KNXIPFrame.TUNNELING_REQUEST)
        # Connection header see KNXnet/IP 4.4.6 TUNNELLING_REQUEST
        body = [0x04, self.channel, self.seq, 0x00]
        if self.seq < 0xff:
            self.seq += 1
        else:
            self.seq = 0
        body.extend(cemi.to_body())
        frame.body = body
        self.data_server.socket.sendto(
            frame.to_frame(), (self.remote_ip, self.remote_port))

        # See KNX specification 3.8.4 chapter 2.6 "Frame confirmation"
        # Send KNX packet 2 times if not acknowledged and close
        # the connection if no ack is received
        res = self.ack_semaphore.acquire(blocking=True, timeout=1)
        # Resend package if not acknowledged after 1 seconds
        if not res:
            self.data_server.socket.sendto(
                frame.to_frame(), (self.remote_ip, self.remote_port))

            res = self.ack_semaphore.acquire(blocking=True, timeout=1)

        # disconnect and reconnect of not acknowledged
        if not res:
            self.disconnect()
            self.connect()

        return res

    def group_read(self, addr, use_cache=True, timeout=1):
        """Send a group read to the KNX bus and return the result."""
        if use_cache:
            res = self.value_cache.get(addr)
            if res:
                logging.debug(
                    "Got value of group address %s from cache: %s", addr, res)
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
        data = self.group_read(addr, use_cache)
        if len(data) != 1:
            problem = "Can't toggle a {}-octet group address {}".format(
                len(data), addr)
            logging.error(problem)
            raise KNXException(problem)

        if data[0] == 0:
            self.group_write(addr, [1])
        elif data[0] == 1:
            self.group_write(addr, [0])
        else:
            problem = "Can't toggle group address {} as value is {}".format(
                addr, data[0])
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

        if not func in listeners:
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
        self.value_cache.set(address, data)
        if self.notify:
            self.notify(address, data)

        try:
            listeners = self.address_listeners[address]
        except KeyError:
            listeners = []

        for listener in listeners:
            listener(address, data)


class DataRequestHandler(SocketServer.BaseRequestHandler):
    """The class that handles incoming UDP packets from the KNX/IP tunnel."""

    def handle(self):
        """Process an incoming package."""
        data = self.request[0]
        sock = self.request[1]

        frame = KNXIPFrame.from_frame(data)

        if frame.service_type_id == KNXIPFrame.TUNNELING_REQUEST:
            req = KNXTunnelingRequest.from_body(frame.body)
            msg = CEMIMessage.from_body(req.cemi)
            send_ack = False

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
            if msg.cmd == CEMIMessage.CMD_GROUP_RESPONSE:
                tunnel.result_queue.put(msg.data)

            if send_ack:
                bodyack = [0x04, req.channel, req.seq, E_NO_ERROR]
                ack = KNXIPFrame(KNXIPFrame.TUNNELLING_ACK)
                ack.body = bodyack
                sock.sendto(ack.to_frame(), self.client_address)

        elif frame.service_type_id == KNXIPFrame.TUNNELLING_ACK:
            logging.debug("Received tunneling ACK")
            self.server.tunnel.ack_semaphore.release()
        elif frame.service_type_id == KNXIPFrame.DISCONNECT_RESPONSE:
            logging.debug("Disconnected")
            self.channel = None
            tunnel = self.server.tunnel
            tunnel.data_server.shutdown()
            tunnel.data_server = None
        elif frame.service_type_id == KNXIPFrame.CONNECTIONSTATE_RESPONSE:
            logging.debug("Connection state response")
            tunnel.connection_state = frame.body[2]
        else:
            logging.info(
                "Message type %s not yet implemented", frame.service_type_id)


class DataServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    """Server that handled the UDP connection to the KNX/IP tunnel."""

    def __init__(self, server_address, RequestHandlerClass, tunnel):
        super(DataServer, self).__init__(server_address, RequestHandlerClass)
        self.tunnel = tunnel
    