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

from cc_modules.cc_db import repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    get_yes_no,
    get_yes_no_none,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    CTV_DICTLIST_INCOMPLETE,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# CAGE
# =============================================================================

class Cage(Task):
    NQUESTIONS = 4
    TASK_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, "CHAR", pv=['Y', 'N'],
        comment_fmt="Q{n}, {s} (Y, N)",
        comment_strings=["C", "A", "G", "E"])
    TASK_FIELDS = [x["name"] for x in TASK_FIELDSPECS]

    @classmethod
    def get_tablename(cls):
        return "cage"

    @classmethod
    def get_taskshortname(cls):
        return "CAGE"

    @classmethod
    def get_tasklongname(cls):
        return "CAGE Questionnaire"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + Cage.TASK_FIELDSPECS

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "CAGE total score",
                "axis_label": "Total score (out of 4)",
                "axis_min": -0.5,
                "axis_max": 4.5,
                "horizontal_lines": [
                    1.5
                ],
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{"content": "CAGE score {}/4".format(self.total_score())}]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/4)"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(Cage.TASK_FIELDS)
            and self.field_contents_valid()
        )

    def get_value(self, q):
        return 1 if getattr(self, "q" + str(q)) == "Y" else 0

    def total_score(self):
        total = 0
        for i in range(1, Cage.NQUESTIONS + 1):
            total += self.get_value(i)
        return total

    def get_task_html(self):
        score = self.total_score()
        exceeds_cutoff = score >= 2
        h = u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 4")
        h += tr_qa(WSTRING("cage_over_threshold"), get_yes_no(exceeds_cutoff))
        h += u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """
        for q in range(1, Cage.NQUESTIONS + 1):
            h += tr_qa(str(q) + u" — " + WSTRING("cage_q" + str(q)),
                       get_yes_no_none(getattr(self, "q" + str(q))))
        h += u"""
            </table>
        """
        return h