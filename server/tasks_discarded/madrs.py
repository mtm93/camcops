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

from cc_task import *

#==============================================================================
# MADRS
#==============================================================================

class Madrs(Task):
    NQUESTIONS = 10
    TASK_FIELDSPECS = repeat_fieldspec("q", 1, NQUESTIONS) + [
        dict(name="period_rated", cctype="TEXT"),
    ]
    TASK_FIELDS = [ x["name"] for x in TASK_FIELDSPECS ]
    
    @classmethod
    def get_tablename(cls):
        return "madrs"
    @classmethod
    def get_taskshortname(cls):
        return "MADRS"
    @classmethod
    def get_tasklongname(cls):
        return u"Montgomery–Åsberg Depression Rating Scale"
    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + CLINICIAN_FIELDSPECS + Madrs.TASK_FIELDSPECS
    
    @classmethod
    def provides_trackers(cls):
        return True
    def get_trackers(self):
        return [
            {
                "value": self.total_score(),
                "plot_label": "MADRS total score",
                "axis_label": "Total score (out of 60)",
                "axis_min": -0.5,
                "axis_max": 60.5,
                "horizontal_lines": [
                    33.5,
                    19.5,
                     6.5,
                ],
                "horizontal_labels": [
                    (35, WSTRING("severe")),
                    (25, WSTRING("moderate")),
                    (14, WSTRING("mild")),
                    ( 3, WSTRING("normal"))
                ]
            }
        ]
    
    def get_summaries(self):
        return [
            dict(name="is_complete", cctype="BOOL", value=self.is_complete() ),
            dict(name="total", cctype="INT", value=self.total_score() ),
        ]

    def is_complete(self):
        return self.are_all_fields_complete(Madrs.TASK_FIELDS)
        
    def total_score(self):
        return self.sum_fields( repeat_fieldname("q", 1, Madrs.NQUESTIONS) )
        
    def get_task_html(self):
        score = self.total_score()
        if score > 34:
            category = WSTRING("severe")
        elif score >= 20:
            category = WSTRING("moderate")
        elif score >= 7:
            category = WSTRING("mild")
        else:
            category = WSTRING("normal")
        ANSWER_DICTS = []
        for q in range(1, Madrs.NQUESTIONS + 1):
            d = { None: "?" }
            for option in range(0, 7):
                if option == 1 or option == 3 or option ==5:
                    d[option] = option
                else:
                    d[option] = WSTRING("madrs_q" + str(q) + "_option" + str(option))
            ANSWER_DICTS.append(d)
        h = self.get_standard_clinician_block() + u"""
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / 60</td></tr>
                    <tr><td>{} <sup>[1]</sup></td><td><b>{}</b></tr>
                </table>
            </div>
            <div class="explanation">
                Ratings are from 0–6 (0 none, 6 extreme problem).
            </div>
            <table class="taskdetail">
                <tr><th width="30%">Question</th><th width="70%">Answer</th></tr>
                <tr><td>{}</td><td><b>{}</b></td></tr>
        """.format(
            self.get_is_complete_tr(),
            WSTRING("total_score"), score,
            WSTRING("category"), category,
            WSTRING("madrs_q_period_rated"), self.period_rated
        )
        for q in range(1, Madrs.NQUESTIONS + 1):
            h += u"""<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                WSTRING("madrs_q" + str(q) + "_s"),
                get_from_dict( ANSWER_DICTS[q - 1], getattr(self, "q" + str(q)) )
            )
        h += u"""
            </table>
            <div class="footnotes">
                [1] Total score &gt;34 severe, &ge;20 moderate, &ge;7 mild, &lt;7 normal.
                (Hermann et al. 1998, PubMed ID 9506602.)
            </div>
        """
        return h