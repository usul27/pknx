import unittest
from knxip.core import *

class KNXIPCoreTestCase(unittest.TestCase):
    """Tests for `core.py`."""
    
    def test_group_address(self):
        """Does the group address parser work correctly?"""
        self.assertEquals(parse_group_address("1"),1)
        self.assertEquals(parse_group_address("1678"),1678)
        self.assertEquals(parse_group_address("1/1"),257)
        self.assertEquals(parse_group_address("2/2"),514)
        self.assertEquals(parse_group_address("0/0/1"),1)
        self.assertEquals(parse_group_address("1/1/1"),2305)
        self.assertEquals(parse_group_address("4/8/45"),10285)

if __name__ == '__main__':
    unittest.main()

