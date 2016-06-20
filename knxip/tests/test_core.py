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

    def test_float_to_knx(self):
        """Does the group address parser work correctly?"""
        
        # See http://www.knx.org/fileadmin/template/documents/downloads_support_menu/KNX_tutor_seminar_page/Advanced_documentation/05_Interworking_E1209.pdf
        self.assertEquals(KNXData.float_to_knx(-30),[0x8a, 0x24]) # example pg. 21/36

        self.assertEquals(KNXData.float_to_knx(0),[0x00, 0x00])
        self.assertEquals(KNXData.float_to_knx(0.01),[0x00, 0x01])
        self.assertEquals(KNXData.float_to_knx(1),[0x00, 0x64])


if __name__ == '__main__':
    unittest.main()

