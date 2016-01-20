#!/usr/bin/env python3
# cc_analytics.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
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
import urllib.error
import urllib.parse
import urllib.request

from .cc_constants import DATEFORMAT
from . import cc_dt
from .cc_logger import logger
from .cc_pls import pls
from . import cc_storedvar
from .cc_unittest import unit_test_ignore
from . import cc_version

ANALYTICS_FREQUENCY_DAYS = 7  # send analytics weekly

ANALYTICS_URL = "https://131.111.177.41/camcops_analytics"
# 131.111.177.41 is egret.psychol.cam.ac.uk, which hosts www.camcops.org.
# Using a numerical IP address saves the DNS lookup step.
# Note that this will fail an SSL validation step, since the site's SSL
# certificate is based on its hostname rather than its IP address; however,
# while the Titanium client complains, Python does what we ask of it.
# We won't use www.camcops.org/something, because that's a redirection address
# and we need direct access.

ANALYTICS_TIMEOUT_MS = 5000

ANALYTICS_PERIOD = datetime.timedelta(days=ANALYTICS_FREQUENCY_DAYS)


def send_analytics_if_necessary():
    """Send analytics to the CamCOPS base server, if required.

    If analytics reporting is enabled, and analytics have not been sent
    recently, collate and send them to the CamCOPS base server in Cambridge,
    UK.
    """
    if not pls.SEND_ANALYTICS:
        # User has disabled analytics reporting.
        return
    lastSentVar = cc_storedvar.ServerStoredVar("lastAnalyticsSentAt", "text",
                                               None)
    lastSentVal = lastSentVar.getValue()
    if lastSentVal:
        elapsed = pls.NOW_UTC_WITH_TZ - cc_dt.get_datetime_from_string(
            lastSentVal)
        if elapsed < ANALYTICS_PERIOD:
            # We sent analytics recently.
            return

    # Compile analytics
    now_as_utc_iso_string = cc_dt.format_datetime(pls.NOW_UTC_WITH_TZ,
                                                  DATEFORMAT.ISO8601)
    (table_names, record_counts) = get_all_tables_with_record_counts()

    # This is what's sent:
    d = {
        "source": "server",
        "now": now_as_utc_iso_string,
        "camcops_version": str(cc_version.CAMCOPS_SERVER_VERSION),
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
        logger.info("Failed to send analytics to {}".format(ANALYTICS_URL))
        return

    # Store current time as last-sent time
    logger.debug("Analytics sent.")
    lastSentVar.setValue(now_as_utc_iso_string)


def get_all_tables_with_record_counts():
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
    return (table_names, record_counts)


def unit_tests():
    """Unit tests for the cc_analytics module."""
    unit_test_ignore("", send_analytics_if_necessary)
    unit_test_ignore("", get_all_tables_with_record_counts)
