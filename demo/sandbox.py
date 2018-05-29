from knxip.conversion import float_to_knx2
from knxip.core import parse_group_address
from knxip.ip import KNXIPTunnel
import logging
import signal
import sys

# setup global logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

def listener(address, data):
    # listener callback for incoming frames
    logging.info('Listener received: address {}, value {}'.format(address, data))

# instanciate tunnel
tunnel = KNXIPTunnel('10.0.0.76')

# register listener for all incoming frames
tunnel.notify = listener

# connect tunnel
tunnel.connect()

# read group addresses
logging.info('Read address 0/0/1: {}'.format(tunnel.group_read(parse_group_address('0/0/1'))))
logging.info('Read address 0/0/2: {}'.format(tunnel.group_read(parse_group_address('0/0/2'))))

# write group addresses
tunnel.group_write(parse_group_address('0/0/1'), [1])
tunnel.group_write(parse_group_address('0/0/2'), [1])

# signal handler disconnecting tunnel and exit program
def signal_handler(signal, frame):
    logging.info('Disconnect tunnel')
    tunnel.disconnect()
    sys.exit(0)

# wait for ctrl+c
signal.signal(signal.SIGINT, signal_handler)
signal.pause()
