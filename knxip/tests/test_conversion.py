'''
Created on Jul 8, 2016

@author: matuschd
'''
import unittest
from knxip.conversion import float_to_knx2, knx2_to_float, \
    knx_to_time, time_to_knx, knx_to_date, date_to_knx, datetime_to_knx,\
    knx_to_datetime
from datetime import time, date, datetime
from knxip.core import KNXException


class KNXConversionTest(unittest.TestCase):

    def test_float_to_knx(self):
        """Does the float to KNX conversion works correctly?"""

        # See
        # http://www.knx.org/fileadmin/template/documents/\
        # downloads_support_menu/KNX_tutor_seminar_page/\
        # Advanced_documentation/05_Interworking_E1209.pdf
        self.assertEquals(float_to_knx2(-30),
                          [0x8a, 0x24])  # example pg. 21/36

        self.assertEquals(float_to_knx2(0), [0x00, 0x00])
        self.assertEquals(float_to_knx2(0.01), [0x00, 0x01])
        self.assertEquals(float_to_knx2(1), [0x00, 0x64])

    def test_knx_to_float(self):
        """Does the KNX to float conversion works correctly?"""

        # example pg. 21/36
        self.assertEquals(knx2_to_float([0x8a, 0x24]), -30)

        self.assertEquals(knx2_to_float([0x00, 0x00]), 0)
        self.assertEquals(knx2_to_float([0x00, 0x01]), 0.01)
        self.assertEquals(knx2_to_float([0x00, 0x64]), 1)

    def test_knx_to_time(self):
        # 17:01:36, no weekday
        self.assertEqual(knx_to_time([0x11, 0x01, 0x24]),
                         [time(17, 1, 36), 0])
        # 17:01:36, weekday=1
        self.assertEqual(knx_to_time([0x31, 0x01, 0x24]),
                         [time(17, 1, 36), 1])
        self.assertRaises(KNXException,
                          knx_to_time, [])
        self.assertRaises(KNXException,
                          knx_to_time, [1, 1, 1, 1])

    def test_time_to_knx(self):
        self.assertEqual(time_to_knx(time(17, 1, 36)),
                         [0x11, 0x01, 0x24])
        self.assertEqual(time_to_knx(time(17, 1, 36), dow=1),
                         [0x31, 0x01, 0x24])

    def test_knx_to_date(self):
        self.assertEqual(knx_to_date([1, 2, 16]),
                         date(2016, 2, 1))
        self.assertEqual(knx_to_date([30, 10, 95]),
                         date(1995, 10, 30))
        self.assertRaises(KNXException,
                          knx_to_date, [])
        self.assertRaises(KNXException,
                          knx_to_date, [1, 1, 1, 1])

    def test_date_to_knx(self):
        self.assertEqual(date_to_knx(date(2016, 2, 1)),
                         [1, 2, 16])
        self.assertEqual(date_to_knx(date(1995, 12, 31)),
                         [31, 12, 95])
        self.assertRaises(KNXException,
                          date_to_knx, date(1989, 1, 1))
        self.assertRaises(KNXException,
                          date_to_knx, date(2100, 10, 30))

    def test_datetime_to_knx(self):
        # 2016/10/30 was a sunday (7)
        # 14:55:23
        # no working day, working day field invalid
        # time = UTC+x
        self.assertEqual(datetime_to_knx(datetime(2016, 10, 30, 14, 55, 23)),
                         [116, 10, 30, 238, 55, 23, 32, 128])
        # 1901/06/07 was a friday (7)
        # 01:10:47
        # no working day, working day field invalid
        # time = UTC+x
        self.assertEqual(datetime_to_knx(datetime(1901, 6, 7, 1, 10, 47)),
                         [1, 6, 7, 161, 10, 47, 97, 128])
        self.assertEqual(datetime_to_knx(datetime(1901, 6, 7, 1, 10, 47),
                                         False),
                         [1, 6, 7, 161, 10, 47, 97, 0])

    def test_knx_to_datetime(self):
        self.assertEqual(knx_to_datetime([1, 6, 7, 161, 10, 47, 97, 128]),
                         datetime(1901, 6, 7, 1, 10, 47))

        self.assertEqual(knx_to_datetime([116, 10, 30, 238, 55, 23, 32, 128]),
                         datetime(2016, 10, 30, 14, 55, 23))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
