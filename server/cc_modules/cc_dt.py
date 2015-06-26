#!/usr/bin/python2.7
# -*- encoding: utf8 -*-

"""
    Copyright (C) 2012-2015 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import datetime
import dateutil
import dateutil.parser
import dateutil.tz
import re
import pytz
# don't use pytz.reference: http://stackoverflow.com/questions/17733139


# =============================================================================
# Processing dates and times
# =============================================================================

def get_datetime_from_string(s):
    """Convert string (e.g. ISO-8601) to datetime, or None."""
    if not s:
        return None  # if you parse() an empty string, you get today's date
    return dateutil.parser.parse(s)  # deals with ISO8601 automatically


def get_date_from_string(s):
    """Convert string (e.g. ISO-8601) to date, or None."""
    if not s:
        return None  # if you parse() an empty string, you get today's date
    return dateutil.parser.parse(s).date()  # deals with ISO8601 automatically


def format_datetime(d, fmt, default=None):
    """Format a datetime with a format string, or return default if None."""
    if d is None:
        return default
    return d.strftime(fmt)


def format_datetime_string(s, fmt, default="(None)"):
    """Converts a string representation of a date (usually from the database)
    into a specified strftime() format."""
    if s is None:
        return default
    dt = get_datetime_from_string(s)
    if dt is None:
        return default
    return dt.strftime(fmt)


def get_date_regex_string(dt):
    # Reminders: ? zero or one, + one or more, * zero or more
    wb = "\\b"  # word boundary; escape the slash
    ws = "\\s"  # whitespace; includes newlines
    # Day, allowing leading zeroes and e.g. "1st, 2nd"
    day = "0*" + str(dt.day) + "(st|nd|rd|th)?"
    # Month, allowing leading zeroes for numeric and e.g. Feb/February
    month_numeric = "0*" + str(dt.month)
    month_word = dt.strftime("%B")
    month_word = month_word[0:3] + "(" + month_word[3:] + ")?"
    month = "(" + month_numeric + "|" + month_word + ")"
    # Year
    year = str(dt.year)
    if len(year) == 4:
        year = "(" + year[0:2] + ")?" + year[2:4]
        # ... makes e.g. (19)?86, to match 1986 or 86
    # Separator: one or more of: whitespace, /, -, comma
    sep = "[" + ws + "/,-]+"
    # ... note that the hyphen has to be at the start or end, otherwise it
    #     denotes a range.
    # Regexes
    basic_regexes = [
        day + sep + month + sep + year,  # e.g. 13 Sep 2014
        month + sep + day + sep + year,  # e.g. Sep 13, 2014
        year + sep + month + sep + day,  # e.g. 2014/09/13
    ]
    return (
        "("
        + "|".join(
            [wb + x + wb for x in basic_regexes]
        )
        + ")"
    )

# Testing:
if False:
    TEST_GET_DATE_REGEX = '''
from __future__ import print_function
import dateutil.parser
import re
testdate = dateutil.parser.parse("7 Jan 2013")
teststring = """
   I was born on 07 Jan 2013, m'lud.
   It was 7 January 13, or 7/1/13, or 1/7/13, or
   Jan 7 2013, or 2013/01/07, or 2013-01-07,
   or 7th January
   13 (split over a line)
   or Jan 7th 13
   or a host of other variations.

   BUT NOT 8 Jan 2013, or 2013/02/07, or 2013
   Jan 17, or just a number like 7, or a month
   like January, or a nonspecific date like
   Jan 2013 or 7 January.
"""
regex_string = get_date_regex_string(testdate)
replacement = "GONE"
r = re.compile(regex_string, re.IGNORECASE)
print(r.sub(replacement, teststring))
'''


def get_date_regex(dt):
    """Regex for anonymisation. Date."""
    return re.compile(get_date_regex_string(dt), re.IGNORECASE)


def get_now_localtz():
    """Get the time now in the local timezone."""
    localtz = dateutil.tz.tzlocal()
    return datetime.datetime.now(localtz)


def get_now_utc():
    """Get the time now in the UTC timezone."""
    return datetime.datetime.now(pytz.utc)


def get_now_utc_notz():
    """Get the UTC time now, but with no timezone information."""
    return get_now_utc().replace(tzinfo=None)


def convert_datetime_to_utc(datetime_tz):
    """Convert date/time with timezone to UTC (with UTC timezone)."""
    return datetime_tz.astimezone(pytz.utc)


def convert_datetime_to_utc_notz(datetime_tz):
    """Convert date/time with timezone to UTC without timezone."""
    # Incoming: date/time with timezone
    utc_tz = datetime_tz.astimezone(pytz.utc)
    return utc_tz.replace(tzinfo=None)


def convert_datetime_to_local(datetime_tz):
    """Convert date/time with timezone to local timezone."""
    # Establish the local timezone
    localtz = dateutil.tz.tzlocal()
    # Convert to local timezone
    return datetime_tz.astimezone(localtz)


def convert_utc_datetime_without_tz_to_local(datetime_utc_notz):
    """Convert UTC date/time without timezone to local timezone."""
    # 1. Make it explicitly in the UTC timezone.
    datetime_utc_tz = datetime_utc_notz.replace(tzinfo=pytz.utc)
    # 2. Establish the local timezone
    localtz = dateutil.tz.tzlocal()
    # 3. Convert to local timezone
    return datetime_utc_tz.astimezone(localtz)


def get_duration_h_m(start_string, end_string, default="N/A"):
    """Calculate the time between two dates/times expressed as strings.

    Return format: string, as one of:
        hh:mm
        -hh:mm
    or
        default parameter
    """
    if start_string is None or end_string is None:
        return default
    start = get_datetime_from_string(start_string)
    end = get_datetime_from_string(end_string)
    duration = end - start  # timedelta: stores days, seconds, microseconds
    # days can be +/-; the others are always +
    minutes = int(round(duration.days * 24*60 + duration.seconds/60))
    (hours, minutes) = divmod(minutes, 60)
    if hours < 0:
        # negative... trickier
        # Python's divmod does interesting things with negative numbers:
        # Hours will be negative, and minutes always positive
        hours += 1
        minutes = 60 - minutes
        return "-{}:{}".format(hours, "00" if minutes == 0 else minutes)
    else:
        return "{}:{}".format(hours, "00" if minutes == 0 else minutes)