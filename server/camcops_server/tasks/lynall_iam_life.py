#!/usr/bin/env python

"""
camcops_server/tasks/lynall_iam_life.py

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

**Lynall M-E — IAM study — life events.**

"""


from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import Task, TaskHasPatientMixin


# =============================================================================
# LynallIamLifeEvents
# =============================================================================

class LynallIamLifeEvents(TaskHasPatientMixin, Task):
    """
    Server implementation of the LynallIamLifeEvents task.
    """
    __tablename__ = "lynall_iam_life"
    shortname = "Lynall_IAM_Life"

    # todo: LynallIamLifeEvents fields

    @staticmethod
    def longname(req: "CamcopsRequest") -> str:
        _ = req.gettext
        return _("Lynall M-E — 2 — IAM — Life events")

    def is_complete(self) -> bool:
        return False  # todo: LynallIamLifeEvents

    def get_task_html(self, req: CamcopsRequest) -> str:
        return ""  # todo: LynallIamLifeEvents