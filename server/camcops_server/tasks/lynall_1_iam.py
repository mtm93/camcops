#!/usr/bin/env python

"""
camcops_server/tasks/lynall_1_iam.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

from typing import Any, Dict, Tuple, Type

import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import (
    bold,
    get_yes_no_none,
    tr_span_col,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import BoolColumn
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin


# =============================================================================
# Lynall1MedicalHistory
# =============================================================================

class Lynall1IamMedicalHistory(TaskHasPatientMixin, Task):
    """
    Server implementation of the Lynall_1_MedicalHistory task.
    """
    __tablename__ = "lynall_1_iam_medicalhistory"
    shortname = "Lynall_1_MedicalHistory"

    # *** fields

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Lynall M-E — 1 — IAM — Medical history")

    def is_complete(self) -> bool:
        return False # ***

    def get_task_html(self, req: CamcopsRequest) -> str:
        return "" # ***
