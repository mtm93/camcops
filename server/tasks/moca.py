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

from cc_modules.cc_constants import PV
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_html import (
    answer,
    italic,
    subheading_spanning_two_columns,
    td,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    CLINICIAN_FIELDSPECS,
    CTV_DICTLIST_INCOMPLETE,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


WORDLIST = ["FACE", "VELVET", "CHURCH", "DAISY", "RED"]


# =============================================================================
# MoCA
# =============================================================================

class Moca(Task):
    NQUESTIONS = 28
    FIELDSPECS = (
        STANDARD_TASK_FIELDSPECS +
        CLINICIAN_FIELDSPECS +
        repeat_fieldspec(
            "q", 1, NQUESTIONS, min=0, max=1,  # see below
            comment_fmt="{s}",
            comment_strings=[
                "Q1 (VSE/path) (0-1)",
                "Q2 (VSE/cube) (0-1)",
                "Q3 (VSE/clock/contour) (0-1)",
                "Q4 (VSE/clock/numbers) (0-1)",
                "Q5 (VSE/clock/hands) (0-1)",
                "Q6 (naming/lion) (0-1)",
                "Q7 (naming/rhino) (0-1)",
                "Q8 (naming/camel) (0-1)",
                "Q9 (attention/5 digits) (0-1)",
                "Q10 (attention/3 digits) (0-1)",
                "Q11 (attention/tapping) (0-1)",
                "Q12 (attention/serial 7s) (0-3)",  # different max
                "Q13 (language/sentence 1) (0-1)",
                "Q14 (language/sentence 2) (0-1)",
                "Q15 (language/fluency) (0-1)",
                "Q16 (abstraction 1) (0-1)",
                "Q17 (abstraction 2) (0-1)",
                "Q18 (recall word/face) (0-1)",
                "Q19 (recall word/velvet) (0-1)",
                "Q20 (recall word/church) (0-1)",
                "Q21 (recall word/daisy) (0-1)",
                "Q22 (recall word/red) (0-1)",
                "Q23 (orientation/date) (0-1)",
                "Q24 (orientation/month) (0-1)",
                "Q25 (orientation/year) (0-1)",
                "Q26 (orientation/day) (0-1)",
                "Q27 (orientation/place) (0-1)",
                "Q28 (orientation/city) (0-1)",
            ]
        ) + [
            dict(name="education12y_or_less", cctype="INT", pv=PV.BIT,
                 comment="<=12 years of education (0 no, 1 yes)"),
            dict(name="trailpicture_blobid", cctype="INT",
                 comment="BLOB ID of trail picture"),
            dict(name="cubepicture_blobid", cctype="INT",
                 comment="BLOB ID of cube picture"),
            dict(name="clockpicture_blobid", cctype="INT",
                 comment="BLOB ID of clock picture"),
        ] +
        repeat_fieldspec(
            "register_trial1_", 1, 5, pv=PV.BIT,
            comment_fmt="Registration, trial 1 (not scored), {n}: {s} "
            "(0 or 1)", comment_strings=WORDLIST) +
        repeat_fieldspec(
            "register_trial2_", 1, 5, pv=PV.BIT,
            comment_fmt="Registration, trial 2 (not scored), {n}: {s} "
            "(0 or 1)", comment_strings=WORDLIST) +
        repeat_fieldspec(
            "recall_category_cue_", 1, 5, pv=PV.BIT,
            comment_fmt="Recall with category cue (not scored), {n}: {s} "
            "(0 or 1)", comment_strings=WORDLIST) +
        repeat_fieldspec(
            "recall_mc_cue_", 1, 5, pv=PV.BIT,
            comment_fmt="Recall with multiple-choice cue (not scored), "
            "{n}: {s} (0 or 1)", comment_strings=WORDLIST) +
        [
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
        ]
    )
    # Fix error above. Hardly elegant!
    for item in FIELDSPECS:
        if item["name"] == "q12":
            item["max"] = 3

    @classmethod
    def get_tablename(cls):
        return "moca"

    @classmethod
    def get_taskshortname(cls):
        return "MoCA"

    @classmethod
    def get_tasklongname(cls):
        return "Montreal Cognitive Assessment"

    @classmethod
    def get_fieldspecs(cls):
        return Moca.FIELDSPECS

    @classmethod
    def get_pngblob_name_idfield_rotationfield_list(self):
        return [
            ("trailpicture", "trailpicture_blobid", None),
            ("cubepicture", "cubepicture_blobid", None),
            ("clockpicture", "clockpicture_blobid", None),
        ]

    @classmethod
    def provides_trackers(cls):
        return True

    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "MOCA total score",
                "axis_label": "Total score (out of 30)",
                "axis_min": -0.5,
                "axis_max": 30.5,
                "horizontal_lines": [
                    25.5,
                ],
                "horizontal_labels": [
                    (26, WSTRING("normal"), "bottom"),
                    (25, WSTRING("abnormal"), "top"),
                ]
            }
        ]

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        return [{
            "content": "MOCA total score {}/30".format(self.total_score())
        }]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/30)"),
            dict(name="category", cctype="TEXT", value=self.category(),
                 comment="Categorization"),
        ]

    def is_complete(self):
        return (
            self.are_all_fields_complete(
                repeat_fieldname("q", 1, Moca.NQUESTIONS))
            and self.field_contents_valid()
        )

    def total_score(self):
        return self.sum_fields(
            repeat_fieldname("q", 1, Moca.NQUESTIONS) +
            ["education12y_or_less"]  # extra point for this
        )

    def score_vsp(self):
        return self.sum_fields(repeat_fieldname("q", 1, 5))

    def score_naming(self):
        return self.sum_fields(repeat_fieldname("q", 6, 8))

    def score_attention(self):
        return self.sum_fields(repeat_fieldname("q", 9, 12))

    def score_language(self):
        return self.sum_fields(repeat_fieldname("q", 13, 15))

    def score_abstraction(self):
        return self.sum_fields(repeat_fieldname("q", 16, 17))

    def score_memory(self):
        return self.sum_fields(repeat_fieldname("q", 18, 22))

    def score_orientation(self):
        return self.sum_fields(repeat_fieldname("q", 23, 28))

    def category(self):
        totalscore = self.total_score()
        return WSTRING("normal") if totalscore >= 26 else WSTRING("abnormal")

    def get_task_html(self):
        vsp = self.score_vsp()
        naming = self.score_naming()
        attention = self.score_attention()
        language = self.score_language()
        abstraction = self.score_abstraction()
        memory = self.score_memory()
        orientation = self.score_orientation()
        totalscore = self.total_score()
        category = self.category()

        h = self.get_standard_clinician_block(True, self.comments) + u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(totalscore) + " / 30")
        h += tr_qa(WSTRING("moca_category") + " <sup>[1]</sup>",
                   category)
        h += u"""
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="69%">Question</th>
                    <th width="31%">Score</th>
                </tr>
        """

        h += tr(WSTRING("moca_subscore_visuospatial"),
                answer(vsp) + " / 5",
                tr_class="subheading")
        h += tr("Path, cube, clock/contour, clock/numbers, clock/hands",
                ", ".join([answer(x) for x in [self.q1, self.q2, self.q3,
                                               self.q4, self.q5]]))

        h += tr(WSTRING("moca_subscore_naming"),
                answer(naming) + " / 3",
                tr_class="subheading")
        h += tr("Lion, rhino, camel",
                ", ".join([answer(x) for x in [self.q6, self.q7, self.q8]]))

        h += tr(WSTRING("moca_subscore_attention"),
                answer(attention) + " / 6",
                tr_class="subheading")
        h += tr("5 digits forwards, 3 digits backwards, tapping, serial 7s "
                "[<i>scores 3</i>]",
                ", ".join([answer(x) for x in [self.q9, self.q10, self.q11,
                                               self.q12]]))

        h += tr(WSTRING("moca_subscore_language"),
                answer(language) + " / 3",
                tr_class="subheading")
        h += tr(u"Repeat sentence 1, repeat sentence 2, fluency to letter ‘F’",
                ", ".join([answer(x) for x in [self.q13, self.q14, self.q15]]))

        h += tr(WSTRING("moca_subscore_abstraction"),
                answer(abstraction) + " / 2",
                tr_class="subheading")
        h += tr("Means of transportation, measuring instruments",
                ", ".join([answer(x) for x in [self.q16, self.q17]]))

        h += tr(WSTRING("moca_subscore_memory"),
                answer(memory) + " / 5",
                tr_class="subheading")
        h += tr(
            "Registered on first trial [<i>not scored</i>]",
            ", ".join([
                answer(x, formatter_answer=italic)
                for x in [
                    self.register_trial1_1,
                    self.register_trial1_2,
                    self.register_trial1_3,
                    self.register_trial1_4,
                    self.register_trial1_5
                ]
            ])
        )
        h += tr(
            "Registered on second trial [<i>not scored</i>]",
            ", ".join([
                answer(x, formatter_answer=italic)
                for x in [
                    self.register_trial2_1,
                    self.register_trial2_2,
                    self.register_trial2_3,
                    self.register_trial2_4,
                    self.register_trial2_5
                ]
            ])
        )
        h += tr(
            "Recall FACE, VELVET, CHURCH, DAISY, RED with no cue",
            ", ".join([
                answer(x) for x in [
                    self.q18, self.q19, self.q20, self.q21, self.q22
                ]
            ])
        )
        h += tr(
            "Recall with category cue [<i>not scored</i>]",
            ", ".join([
                answer(x, formatter_answer=italic)
                for x in [
                    self.recall_category_cue_1,
                    self.recall_category_cue_2,
                    self.recall_category_cue_3,
                    self.recall_category_cue_4,
                    self.recall_category_cue_5
                ]
            ])
        )
        h += tr(
            "Recall with multiple-choice cue [<i>not scored</i>]",
            ", ".join([
                answer(x, formatter_answer=italic)
                for x in [
                    self.recall_mc_cue_1,
                    self.recall_mc_cue_2,
                    self.recall_mc_cue_3,
                    self.recall_mc_cue_4,
                    self.recall_mc_cue_5
                ]
            ])
        )

        h += tr(WSTRING("moca_subscore_orientation"),
                answer(orientation) + " / 6",
                tr_class="subheading")
        h += tr(
            "Date, month, year, day, place, city",
            ", ".join([
                answer(x) for x in [
                    self.q23, self.q24, self.q25, self.q26, self.q27, self.q28
                ]
            ])
        )

        h += subheading_spanning_two_columns(WSTRING("moca_education_s"))
        h += tr_qa(u"≤12 years’ education?", self.education12y_or_less)
        h += u"""
            </table>
            <table class="taskdetail">
        """
        h += subheading_spanning_two_columns(
            "Images of tests: trail, cube, clock",
            th_not_td=True)
        h += tr(
            td(self.get_blob_png_html(self.trailpicture_blobid),
               td_class="photo", td_width="50%"),
            td(self.get_blob_png_html(self.cubepicture_blobid),
               td_class="photo", td_width="50%"),
            literal=True,
        )
        h += tr(
            td(self.get_blob_png_html(self.trailpicture_blobid),
               td_class="photo", td_width="50%"),
            td("", td_class="subheading"),
            literal=True,
        )
        h += u"""
            </table>
            <div class="footnotes">
                [1] Normal is ≥26 (Nasreddine et al. 2005, PubMed ID 15817019).
            </div>
            <div class="copyright">
                MoCA: Copyright © Ziad Nasreddine.
                May be reproduced without permission for CLINICAL and
                EDUCATIONAL use. You must obtain permission from the copyright
                holder for any other use.
            </div>
        """
        return h