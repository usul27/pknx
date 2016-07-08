'''
Created on Jul 8, 2016

@author: matuschd
'''
import unittest
from knxip.conversion import float_to_knx


class KNXConversionTest(unittest.TestCase):

    def test_float_to_knx(self):
        """Does the group address parser work correctly?"""

        # See
        # http://www.knx.org/fileadmin/template/documents/\
        # downloads_support_menu/KNX_tutor_seminar_page/\
        # Advanced_documentation/05_Interworking_E1209.pdf
        self.assertEquals(float_to_knx(-30),
                          [0x8a, 0x24])  # example pg. 21/36

        self.assertEquals(float_to_knx(0), [0x00, 0x00])
        self.assertEquals(float_to_knx(0.01), [0x00, 0x01])
        self.assertEquals(float_to_knx(1), [0x00, 0x64])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
