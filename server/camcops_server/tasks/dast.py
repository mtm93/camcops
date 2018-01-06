#!/usr/bin/env python
# camcops_server/tasks/camcops_server/tasks/dast.py

"""
===============================================================================
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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
from sqlalchemy.sql.sqltypes import Integer

from camcops_server.cc_modules.cc_ctvinfo import CTV_INCOMPLETE, CtvInfo
from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_html import (
    answer,
    get_yes_no,
    tr,
    tr_qa,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_sqla_coltypes import CharColType
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# DAST
# =============================================================================

class DastMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Dast'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "q", 1, cls.NQUESTIONS, CharColType,
            pv=['Y', 'N'],
            comment_fmt='Q{n}. {s} ("+" = Y scores 1, "-" = N scores 1)',
            comment_strings=[
                "non-medical drug use (+)",
                "abused prescription drugs (+)",
                "abused >1 drug at a time (+)",
                "get through week without drugs (-)",
                "stop when want to (-)",
                "abuse drugs continuously (+)",
                "try to limit to certain situations (-)",
                "blackouts/flashbacks (+)",
                "feel bad about drug abuse (-)",
                "spouse/parents complain (+)",
                "friends/relative know/suspect (+)",
                "caused problems with spouse (+)",
                "family sought help (+)",
                "lost friends (+)",
                "neglected family/missed work (+)",
                "trouble at work (+)",
                "lost job (+)",
                "fights under influence (+)",
                "arrested for unusual behaviour under influence (+)",
                "arrested for driving under influence (+)",
                "illegal activities to obtain (+)",
                "arrested for possession (+)",
                "withdrawal symptoms (+)",
                "medical problems (+)",
                "sought help (+)",
                "hospital for medical problems (+)",
                "drug treatment program (+)",
                "outpatient treatment for drug abuse (+)",
            ]
        )
        super().__init__(name, bases, classdict)


class Dast(TaskHasPatientMixin, Task,
           metaclass=DastMetaclass):
    __tablename__ = "dast"
    shortname = "DAST"
    longname = "Drug Abuse Screening Test"
    provides_trackers = True

    NQUESTIONS = 28
    TASK_FIELDS = strseq("q", 1, NQUESTIONS)

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="DAST total score",
            axis_label="Total score (out of {})".format(self.NQUESTIONS),
            axis_min=-0.5,
            axis_max=self.NQUESTIONS + 0.5,
            horizontal_lines=[10.5, 5.5]
        )]

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="DAST total score {}/{}".format(self.total_score(),
                                                    self.NQUESTIONS)
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(name="total",
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(Dast.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def get_score(self, q: int) -> int:
        yes = "Y"
        value = getattr(self, "q" + str(q))
        if value is None:
            return 0
        if q == 4 or q == 5 or q == 7:
            return 0 if value == yes else 1
        else:
            return 1 if value == yes else 0

    def total_score(self) -> int:
        total = 0
        for q in range(1, Dast.NQUESTIONS + 1):
            total += self.get_score(q)
        return total

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        exceeds_cutoff_1 = score >= 6
        exceeds_cutoff_2 = score >= 11
        main_dict = {
            None: None,
            "Y": req.wappstring("yes"),
            "N": req.wappstring("no")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr(req)
        h += tr(req.wappstring("total_score"),
                answer(score) + " / {}".format(self.NQUESTIONS))
        h += tr_qa(self.wxstring(req, "exceeds_standard_cutoff_1"),
                   get_yes_no(req, exceeds_cutoff_1))
        h += tr_qa(self.wxstring(req, "exceeds_standard_cutoff_2"),
                   get_yes_no(req, exceeds_cutoff_2))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """
        for q in range(1, Dast.NQUESTIONS + 1):
            h += tr(
                self.wxstring(req, "q" + str(q)),
                answer(get_from_dict(main_dict, getattr(self, "q" + str(q)))) +
                " — " + answer(str(self.get_score(q)))
            )
        h += """
            </table>
            <div class="copyright">
                DAST: Copyright © Harvey A. Skinner and the Centre for
                Addiction and Mental Health, Toronto, Canada.
                Reproduced here under the permissions granted for
                NON-COMMERCIAL use only. You must obtain permission from the
                copyright holder for any other use.
            </div>
        """
        return h
