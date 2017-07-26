#!/usr/bin/env python
# cc_analytics.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================
"""

import datetime
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Tuple

from .cc_constants import DATEFORMAT
from .cc_dt import (
    format_datetime,
    get_datetime_from_string,
)
from .cc_pls import pls
from .cc_storedvar import ServerStoredVar
from .cc_unittest import unit_test_ignore
from .cc_version import CAMCOPS_SERVER_VERSION

log = logging.getLogger(__name__)

ANALYTICS_FREQUENCY_DAYS = 7  # send analytics weekly

ANALYTICS_URL = "https://egret.psychol.cam.ac.uk/camcops_analytics"
# 131.111.177.41 is egret.psychol.cam.ac.uk, which hosts www.camcops.org.
# Using a numerical IP address saves the DNS lookup step, but fails SSL
# validation (which, in some Python settings, raises an exception).

ANALYTICS_TIMEOUT_MS = 5000

ANALYTICS_PERIOD = datetime.timedelta(days=ANALYTICS_FREQUENCY_DAYS)


def send_analytics_if_necessary() -> None:
    """Send analytics to the CamCOPS base server, if required.

    If analytics reporting is enabled, and analytics have not been sent
    recently, collate and send them to the CamCOPS base server in Cambridge,
    UK.
    """
    if not pls.SEND_ANALYTICS:
        # User has disabled analytics reporting.
        return
    last_sent_var = ServerStoredVar("lastAnalyticsSentAt",
                                    ServerStoredVar.TYPE_TEXT,
                                    None)
    last_sent_val = last_sent_var.get_value()
    if last_sent_val:
        elapsed = pls.NOW_UTC_WITH_TZ - get_datetime_from_string(
            last_sent_val)
        if elapsed < ANALYTICS_PERIOD:
            # We sent analytics recently.
            return

    # Compile analytics
    now_as_utc_iso_string = format_datetime(pls.NOW_UTC_WITH_TZ,
                                            DATEFORMAT.ISO8601)
    (table_names, record_counts) = get_all_tables_with_record_counts()

    # This is what's sent:
    d = {
        "source": "server",
        "now": now_as_utc_iso_string,
        "camcops_version": str(CAMCOPS_SERVER_VERSION),
        "server": pls.SERVER_NAME,
        "table_names": ",".join(table_names),
        "record_counts": ",".join([str(x) for x in record_counts]),
    }
    # The HTTP_HOST variable might provide some extra information, but is
    # per-request rather than per-server, making analytics involving it that
    # bit more intrusive for little extra benefit, so let's not send it.
    # See http://stackoverflow.com/questions/2297403 for details.

    # Send it.
    encoded_dict = urllib.parse.urlencode(d).encode('ascii')
    request = urllib.request.Request(ANALYTICS_URL, encoded_dict)
    try:
        urllib.request.urlopen(request, timeout=ANALYTICS_TIMEOUT_MS)
        # don't care about any response
    except (urllib.error.URLError, urllib.error.HTTPError):
        # something broke; try again next time
        log.info("Failed to send analytics to {}".format(ANALYTICS_URL))
        return

    # Store current time as last-sent time
    log.debug("Analytics sent.")
    last_sent_var.set_value(now_as_utc_iso_string)


def get_all_tables_with_record_counts() -> Tuple[List[str], List[int]]:
    """Returns all database table names ad their associated record counts.

    Returns a tuple (table_names, record_counts); the first element is a
    list of table names, and the second is a list of associated record counts.
    """
    table_names = pls.db.get_all_table_names()
    record_counts = []
    for table in table_names:
        # column_names = pls.db.fetch_column_names(table)
        # No need to distinguish current/non-current, since the "*_current"
        # views do that already.
        record_counts.append(pls.db.count_where(table))  # count all records
    return table_names, record_counts


def ccanalytics_unit_tests() -> None:
    """Unit tests for the cc_analytics module."""
    unit_test_ignore("", send_analytics_if_necessary)
    unit_test_ignore("", get_all_tables_with_record_counts)
