import unittest
import logging
import sys
from knxip.gatewayscanner import gatewayscanner


class test_gatewayscanner(unittest.TestCase):
    """Tests for `core.py`."""

    def test_tryScan(self):
        x = gatewayscanner()
        x.start_search()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.StreamHandler(sys.stdout)
    unittest.main()