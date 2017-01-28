#!/usr/bin/env python
# cc_version.py

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

from typing import Union

from semantic_version import Version
from .cc_version_string import (
    CAMCOPS_SERVER_VERSION_STRING,
    MINIMUM_TABLET_VERSION_STRING,
)

# =============================================================================
# Version constants and configuration variables read by shell scripts
# =============================================================================

CAMCOPS_SERVER_VERSION = Version(CAMCOPS_SERVER_VERSION_STRING)
MINIMUM_TABLET_VERSION = Version(MINIMUM_TABLET_VERSION_STRING)


# =============================================================================
# For converting from older formats
# =============================================================================

def make_version(v: Union[str, float, None]) -> Version:
    if v is None:
        return Version("0.0.0")
    vstr = str(v)
    # - Note that Version.coerce(vstr) will handle "1.1.1" and "1.1", but not
    #   e.g. "1.06" (it will complain about leading zeroes).
    # - Furthermore, "1.5" -> (1, 5, 0) whilst "1.14" -> (1, 14, 0), which
    #   doesn't fit float ordering.
    # - So:
    try:
        # Deal with something that's already in semantic numbering format.
        return Version(vstr)
    except ValueError:
        parts = vstr.split(".")
        # Easy:
        major = int(parts[0]) if len(parts) > 0 else 0
        # Defaults:
        patch = 0
        if len(parts) == 2:  # e.g. "1.06"
            # More tricky: older versions followed float rules, so 1.14 < 1.5.
            # The only way of dealing with this is to enforce a number
            # of digits/decimal places, so either:
            # (a) 1.14 -> "1.14.0" and 1.5 -> "1.50.0", or
            # (b) 1.14 -> "1.1.4" and 1.5 -> "1.5.0"
            # The decision is arbitrary as long as we right-pad everything
            after_dp = parts[1]
            max_minor_digits = 2  # the most we used
            minor = int(after_dp.ljust(max_minor_digits, "0"))
            # "x".ljust(3, "0") -> "x00"
        else:
            raise
        return Version("{}.{}.{}".format(major, minor, patch))


# =============================================================================
# Notable previous versions
# =============================================================================

TABLET_VERSION_2_0_0 = Version("2.0.0")  # move to C++ version, 2016-2017
