'''
Created on Jul 3, 2016

@author: matuschd
'''
import unittest

from knxip.ip import KNXIPTunnel


class TestKNXIPTunnel(unittest.TestCase):


    def testConnect(self):
        # Try to connect to an auto-discovered KNX gateway
        tunnel = KNXIPTunnel("0.0.0.0")
        tunnel.connect()
        tunnel.disconnect()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testConnect']
    unittest.main()