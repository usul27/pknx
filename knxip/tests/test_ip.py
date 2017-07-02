'''
Created on Jul 3, 2016

@author: matuschd
'''
import unittest
import time
import os
from datetime import datetime

from knxip.ip import KNXIPTunnel

# If a KNX gateway IP is set in the environment, use this
gwip = os.environ.get('GWIP')
if gwip is None:
    gwip = "0.0.0.0"
print("Using KNX Gateway IP ",gwip)


class TestKNXIPTunnel(unittest.TestCase):

    def testConnect(self):
        """Test if the system can connect to an auto-discovered gateway"""
        # Try to connect to an auto-discovered KNX gateway
        tunnel = KNXIPTunnel(gwip)
        self.assertTrue(tunnel.connect())
        tunnel.disconnect()

        # Try to connect to a non-existing gateway
        # Check if the timeout works as expected
        tunnel = KNXIPTunnel("240.0.0.0")
        tick = datetime.now()
        self.assertFalse(tunnel.connect(2))
        tock = datetime.now()
        diff = tock - tick    # the result is a datetime.timedelta object
        self.assertTrue(diff.total_seconds() >= 1 and diff.total_seconds() < 3)

    def testAutoConnect(self):
        """Test if the KNX tunnel will be automatically connected."""
        tunnel = KNXIPTunnel(gwip)
        self.assertFalse(tunnel.connected)
        tunnel.group_read(1)
        self.assertTrue(tunnel.connected)
        
        
    def testKeepAlive(self):
        """Test if the background thread runs and updated the state"""
        tunnel = KNXIPTunnel(gwip)
        self.assertTrue(tunnel.connect())
        # Background thread should reset this to 0 if the connection is still
        # alive
        tunnel.connection_state=1
        time.sleep(66)
        self.assertEqual(tunnel.connection_state,0)        

    def testReadTimeout(self):
        """Test if read timeouts work and group_read operations

        group_read operations should never block
        """
        tunnel = KNXIPTunnel(gwip)
        tunnel.connect()

        # Read from some random address and hope nothing responds here
        tick = datetime.now()
        res = tunnel.group_read(37000, timeout=1)
        tock = datetime.now()
        diff = tock - tick    # the result is a datetime.timedelta object
        self.assertTrue(diff.total_seconds() >= 1 and diff.total_seconds() < 3)
        self.assertIsNone(res)

        # Read from some random address and hope nothing responds here
        tick = datetime.now()
        res = tunnel.group_read(37000, timeout=5)
        tock = datetime.now()
        diff = tock - tick    # the result is a datetime.timedelta object
        self.assertTrue(diff.total_seconds() >= 5 and diff.total_seconds() < 6)
        self.assertIsNone(res)

        tunnel.disconnect()

    def testCleanup(self):
        """Test of disconnect works fine

        Makes sure that there are no connections left open
        """
        for _i in range(0, 10):
            # Try to connect to an auto-discovered KNX gateway
            tunnel = KNXIPTunnel(gwip)
            tunnel.connect()
            tunnel.disconnect()

    def testListeners(self):
        """Test if listeners can be registered and unregistered."""

        def message_received(address, data):
            pass

        tunnel = KNXIPTunnel(gwip)
        tunnel.register_listener(0, message_received)
        res = tunnel.unregister_listener(0, message_received)
        assert(res)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testConnect']
    unittest.main()
