#!/usr/bin/env python
# camcops_server/tasks/wsas.py

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

from typing import Any, Dict, List, Tuple, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, Integer

from ..cc_modules.cc_constants import DATA_COLLECTION_UNLESS_UPGRADED_DIV
from ..cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from ..cc_modules.cc_db import add_multiple_columns
from ..cc_modules.cc_html import answer, get_true_false, tr, tr_qa
from ..cc_modules.cc_request import CamcopsRequest
from ..cc_modules.cc_sqlalchemy import Base
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import get_from_dict, Task, TaskHasPatientMixin
from ..cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# WSAS
# =============================================================================

class WsasMetaClass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Wsas'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS,
            minimum=cls.MIN_PER_Q, maximum=cls.MAX_PER_Q,
            comment_fmt="Q{n}, {s} (0-4, higher worse)",
            comment_strings=[
                "work",
                "home management",
                "social leisure",
                "private leisure",
                "relationships",
            ]
        )
        super().__init__(name, bases, classdict)


class Wsas(TaskHasPatientMixin, Task, Base,
           metaclass=WsasMetaClass):
    __tablename__ = "wsas"
    shortname = "WSAS"
    longname = "Work and Social Adjustment Scale"
    provides_trackers = True

    retired_etc = Column(
        "retired_etc", Boolean,
        comment="Retired or choose not to have job for reason unrelated "
                "to problem"
    )

    MIN_PER_Q = 0
    MAX_PER_Q = 8
    NQUESTIONS = 5
    QUESTION_FIELDS = strseq("q", 1, NQUESTIONS)
    TASK_FIELDS = QUESTION_FIELDS + ["retired_etc"]
    MAX_TOTAL = MAX_PER_Q * NQUESTIONS

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="WSAS total score (lower is better)",
            axis_label="Total score (out of {})".format(self.MAX_TOTAL),
            axis_min=-0.5,
            axis_max=self.MAX_TOTAL + 0.5
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(
                name="total_score",
                coltype=Integer(),
                value=self.total_score(),
                comment="Total score (/ {})".format(self.MAX_TOTAL)),
        ]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(content="WSAS total score {t}/{tm}".format(
            t=self.total_score(), tm=self.MAX_TOTAL)
        )]

    def total_score(self) -> int:
        return self.sum_fields(self.QUESTION_FIELDS)

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.QUESTION_FIELDS) and
            self.field_contents_valid()
        )

    def get_task_html(self, req: CamcopsRequest) -> str:
        option_dict = {None: None}
        for a in range(self.MIN_PER_Q, self.MAX_PER_Q + 1):
            option_dict[a] = req.wappstring("wsas_a" + str(a))
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr>
                        <td>Total score</td>
                        <td>{total} / 40</td>
                    </td>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="75%">Question</th>
                    <th width="25%">Answer</th>
                </tr>
                {retired_row}
            </table>
            <table class="taskdetail">
                <tr>
                    <th width="75%">Question</th>
                    <th width="25%">Answer (0–8)</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(),
            total=answer(self.total_score()),
            retired_row=tr_qa(self.wxstring(req, "q_retired_etc"),
                              get_true_false(self.retired_etc)),
        )
        for q in range(1, self.NQUESTIONS + 1):
            a = getattr(self, "q" + str(q))
            fa = get_from_dict(option_dict, a) if a is not None else None
            h += tr(self.wxstring(req, "q" + str(q)), answer(fa))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
