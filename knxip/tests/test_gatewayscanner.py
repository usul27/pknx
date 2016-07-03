import unittest
import logging
import sys
from knxip.gatewayscanner import GatewayScanner


class test_GatewayScanner(unittest.TestCase):
    """Tests for `gatewayscanner.py`."""

    def test_tryScan(self):
        desired_port = 3671
        sc = GatewayScanner()
        result = sc.start_search()
        print("Received Gateay: {}:{}".format(result[0], result[1]))
        self.assertEqual(desired_port, result[1])


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.StreamHandler(sys.stdout)
    unittest.main()
