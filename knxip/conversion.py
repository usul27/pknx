"""Conversions between KNX data types and native Python types"""

from datetime import time, date, datetime, timedelta
from knxip.core import KNXException


def float_to_knx2(floatval):
    """Convert a float to a 2 byte KNX float value"""

    if floatval < -671088.64 or floatval > 670760.96:
        raise KNXException("float {} out of valid range".format(floatval))

    floatval = floatval * 100

    for i in range(0, 15):
        exp = pow(2, i)
        if ((floatval / exp) >= -2048) and ((floatval / exp) < 2047):
            break

    if floatval < 0:
        sign = 1
        mantisse = int(2048 + (floatval / exp))
    else:
        sign = 0
        mantisse = int(floatval / exp)

    return [(sign << 7) + (i << 3) + (mantisse >> 8),
            mantisse & 0xff]


def knx2_to_float(knxdata):
    """Convert a KNX 2 byte float object to a float"""
    if len(knxdata) != 2:
        raise KNXException("Can only convert a 2 Byte object to float")

    data = knxdata[0] * 256 + knxdata[1]
    sign = data >> 15
    exponent = (data >> 11) & 0x0f
    mantisse = float(data & 0x7ff)
    if sign == 1:
        mantisse = -2048 + mantisse

    return mantisse * pow(2, exponent) / 100


def time_to_knx(timeval, dow=0):
    """Converts a time and day-of-week to a KNX time object"""

    knxdata = [0, 0, 0]
    knxdata[0] = ((dow & 0x07) << 5) + timeval.hour
    knxdata[1] = timeval.minute
    knxdata[2] = timeval.second
    return knxdata


def knx_to_time(knxdata):
    """Converts a KNX time to a tuple of a time object and the day of week"""

    if len(knxdata) != 3:
        raise KNXException("Can only convert a 3 Byte object to time")

    dow = knxdata[0] >> 5
    res = time(knxdata[0] & 0x1f, knxdata[1], knxdata[2])

    return [res, dow]


def date_to_knx(dateval):
    """Convert a date to a 3 byte KNX data array"""

    if (dateval.year < 1990) or (dateval.year > 2089):
        raise KNXException("Year has to be between 1990 and 2089")

    if dateval.year < 2000:
        year = dateval.year - 1900
    else:
        year = dateval.year - 2000

    return([dateval.day, dateval.month, year])


def knx_to_date(knxdata):
    """Convert a 3 byte KNX data object to a date"""

    if len(knxdata) != 3:
        raise KNXException("Can only convert a 3 Byte object to date")

    year = knxdata[2]
    if year >= 90:
        year += 1900
    else:
        year += 2000

    return date(year, knxdata[1], knxdata[0])


def datetime_to_knx(datetimeval, clock_synced_external=1):
    """Convert a Python timestamp to an 8 byte KNX time and date object"""

    res = [0, 0, 0, 0, 0, 0, 0, 0]
    year = datetimeval.year
    if ((year < 1900) or (year > 2155)):
        raise KNXException("Only years between 1900 and 2155 supported")
    res[0] = year - 1900
    res[1] = datetimeval.month
    res[2] = datetimeval.day
    res[3] = (datetimeval.isoweekday() << 5) + datetimeval.hour
    res[4] = datetimeval.minute
    res[5] = datetimeval.second
    if datetimeval.isoweekday() < 6:
        is_working_day = 1
    else:
        is_working_day = 0

    # DST starts last Sunday in March
    d = datetime(year, 4, 1)
    dston = d - timedelta(days=d.weekday() + 1)
    # ends last Sunday in October
    d = datetime(year, 11, 1)
    dstoff = d - timedelta(days=d.weekday() + 1)
    if dston <= datetimeval.replace(tzinfo=None) < dstoff:
        dst = 1
    else:
        dst = 0

    res[6] = (is_working_day << 6) + (1 << 5) + dst
    if (clock_synced_external):
        res[7] = 128
    else:
        res[7] = 0

    return res


def knx_to_datetime(knxdata):
    """Convert a an 8 byte KNX time and date object to its components"""

    if len(knxdata) != 8:
        raise KNXException("Can only convert an 8 Byte object to datetime")

    year = knxdata[0] + 1900
    month = knxdata[1]
    day = knxdata[2]
    hour = knxdata[3] & 0x1f
    minute = knxdata[4]
    second = knxdata[5]

    return datetime(year, month, day, hour, minute, second)


def string_to_knx(str):
    """Converts a string to its KNX presentation

    This function will truncate the string to a maximum of 14 characters
    and remove all characters that can't be represented by the KNX character
    set
    """

    # TODO
    pass


def knx_to_string(knxdata):
    """Convert a KNX 14-byte string object to a Python string"""

    # TODO
    pass
