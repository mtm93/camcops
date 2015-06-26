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

import pythonlib.rnc_web as ws
from cc_modules.cc_constants import DATEFORMAT, PV
from cc_modules.cc_dt import format_datetime_string
from cc_modules.cc_html import (
    get_present_absent_none,
    heading_spanning_two_columns,
    subheading_spanning_two_columns,
    tr_qa,
)
from cc_modules.cc_lang import is_false
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    CLINICIAN_FIELDSPECS,
    CTV_DICTLIST_INCOMPLETE,
    ICD10_COPYRIGHT_DIV,
    STANDARD_TASK_FIELDSPECS,
    Task,
)


# =============================================================================
# Icd10Manic
# =============================================================================

class Icd10Manic(Task):
    CORE_FIELDSPECS = [
        dict(name="mood_elevated", cctype="BOOL", pv=PV.BIT,
             comment="The mood is 'elevated' [hypomania] or 'predominantly "
             "elevated [or] expansive' [mania] to a degree that is definitely "
             "abnormal for the individual concerned."),
        dict(name="mood_irritable", cctype="BOOL", pv=PV.BIT,
             comment="The mood is 'irritable' [hypomania] or 'predominantly "
             "irritable' [mania] to a degree that is definitely abnormal for "
             "the individual concerned."),
    ]
    HYPOMANIA_MANIA_FIELDSPECS = [
        dict(name="distractible", cctype="BOOL", pv=PV.BIT,
             comment="Difficulty in concentration or distractibility [from "
             "the criteria for hypomania]; distractibility or constant "
             "changes in activity or plans [from the criteria for mania]."),
        dict(name="activity", cctype="BOOL", pv=PV.BIT,
             comment="Increased activity or physical restlessness."),
        dict(name="sleep", cctype="BOOL", pv=PV.BIT,
             comment="Decreased need for sleep."),
        dict(name="talkativeness", cctype="BOOL", pv=PV.BIT,
             comment="Increased talkativeness (pressure of speech)."),
        dict(name="recklessness", cctype="BOOL", pv=PV.BIT,
             comment="Mild spending sprees, or other types of reckless or "
             "irresponsible behaviour [hypomania]; behaviour which is "
             "foolhardy or reckless and whose risks the subject does not "
             "recognize e.g. spending sprees, foolish enterprises, reckless "
             "driving [mania]."),
        dict(name="social_disinhibition", cctype="BOOL", pv=PV.BIT,
             comment="Increased sociability or over-familiarity [hypomania]; "
             "loss of normal social inhibitions resulting in behaviour which "
             "is inappropriate to the circumstances [mania]."),
        dict(name="sexual", cctype="BOOL", pv=PV.BIT,
             comment="Increased sexual energy [hypomania]; marked sexual "
             "energy or sexual indiscretions [mania]."),
    ]
    MANIA_FIELDSPECS = [
        dict(name="grandiosity", cctype="BOOL", pv=PV.BIT,
             comment="Inflated self-esteem or grandiosity."),
        dict(name="flight_of_ideas", cctype="BOOL", pv=PV.BIT,
             comment="Flight of ideas or the subjective experience of "
             "thoughts racing."),
    ]
    OTHER_CRITERIA_FIELDSPECS = [
        dict(name="sustained4days", cctype="BOOL", pv=PV.BIT,
             comment="Elevated/irritable mood sustained for at least 4 days."),
        dict(name="sustained7days", cctype="BOOL", pv=PV.BIT,
             comment="Elevated/irritable mood sustained for at least 7 days."),
        dict(name="admission_required", cctype="BOOL", pv=PV.BIT,
             comment="Elevated/irritable mood severe enough to require "
             "hospital admission."),
        dict(name="some_interference_functioning", cctype="BOOL",
             pv=PV.BIT, comment="Some interference with personal functioning "
             "in daily living."),
        dict(name="severe_interference_functioning", cctype="BOOL",
             pv=PV.BIT, comment="Severe interference with personal "
             "functioning in daily living."),
    ]
    PSYCHOSIS_FIELDSPECS = [
        dict(name="perceptual_alterations", cctype="BOOL", pv=PV.BIT,
             comment="Perceptual alterations (e.g. subjective hyperacusis, "
             "appreciation of colours as specially vivid, etc.)."),
        # ... not psychotic
        dict(name="hallucinations_schizophrenic", cctype="BOOL",
             pv=PV.BIT,
             comment="Hallucinations that are 'typically schizophrenic' "
             "(hallucinatory voices giving a running commentary on the "
             "patient's behaviour, or discussing him between themselves, or "
             "other types of hallucinatory voices coming from some part of "
             "the body)."),
        dict(name="hallucinations_other", cctype="BOOL", pv=PV.BIT,
             comment="Hallucinations (of any other kind)."),
        dict(name="delusions_schizophrenic", cctype="BOOL", pv=PV.BIT,
             comment="Delusions that are 'typically schizophrenic' (delusions "
             "of control, influence or passivity, clearly referred to body or "
             "limb movements or specific thoughts, actions, or sensations; "
             "delusional perception; persistent delusions of other kinds that "
             "are culturally inappropriate and completely impossible)."),
        dict(name="delusions_other", cctype="BOOL", pv=PV.BIT,
             comment="Delusions (of any other kind)."),
    ]
    CORE_NAMES = [x["name"] for x in CORE_FIELDSPECS]
    HYPOMANIA_MANIA_NAMES = [x["name"] for x in HYPOMANIA_MANIA_FIELDSPECS]
    MANIA_NAMES = [x["name"] for x in MANIA_FIELDSPECS]
    OTHER_CRITERIA_NAMES = [x["name"] for x in OTHER_CRITERIA_FIELDSPECS]
    PSYCHOSIS_NAMES = [x["name"] for x in PSYCHOSIS_FIELDSPECS]
    TASK_FIELDSPECS = (
        CLINICIAN_FIELDSPECS
        + [
            dict(name="date_pertains_to", cctype="ISO8601",
                 comment="Date the assessment pertains to"),
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
        ]
        + CORE_FIELDSPECS
        + HYPOMANIA_MANIA_FIELDSPECS
        + MANIA_FIELDSPECS
        + OTHER_CRITERIA_FIELDSPECS
        + PSYCHOSIS_FIELDSPECS
    )

    @classmethod
    def get_tablename(cls):
        return "icd10manic"

    @classmethod
    def get_taskshortname(cls):
        return "ICD10-MANIC"

    @classmethod
    def get_tasklongname(cls):
        return (
            u"ICD-10 symptomatic criteria for a manic/hypomanic episode "
            u"(as in e.g. F06.3, F25, F30, F31)"
        )

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + Icd10Manic.TASK_FIELDSPECS

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        dl = [{
            "content": "Pertains to: {}. Category: {}.".format(
                format_datetime_string(self.date_pertains_to,
                                       DATEFORMAT.LONG_DATE),
                self.get_description()
            )
        }]
        if self.comments:
            dl.append({"content": ws.webify(self.comments)})
        return dl

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="category", cctype="TEXT",
                 value=self.get_description(),
                 comment="Diagnostic category"),
            dict(name="psychotic_symptoms", cctype="BOOL",
                 value=self.psychosis_present(),
                 comment="Psychotic symptoms present?"),
        ]

    # Meets criteria? These also return null for unknown.
    def meets_criteria_mania_psychotic_schizophrenic(self):
        x = self.meets_criteria_mania_ignoring_psychosis()
        if not x:
            return x
        if self.hallucinations_other or self.delusions_other:
            return False  # that counts as manic psychosis
        if self.hallucinations_other is None or self.delusions_other is None:
            return None  # might be manic psychosis
        if self.hallucinations_schizophrenic or self.delusions_schizophrenic:
            return True
        if (self.hallucinations_schizophrenic is None
                or self.delusions_schizophrenic is None):
            return None
        return False

    def meets_criteria_mania_psychotic_icd(self):
        x = self.meets_criteria_mania_ignoring_psychosis()
        if not x:
            return x
        if self.hallucinations_other or self.delusions_other:
            return True
        if self.hallucinations_other is None or self.delusions_other is None:
            return None
        return False

    def meets_criteria_mania_nonpsychotic(self):
        x = self.meets_criteria_mania_ignoring_psychosis()
        if not x:
            return x
        if (self.hallucinations_schizophrenic is None
                or self.delusions_schizophrenic is None
                or self.hallucinations_other is None
                or self.delusions_other is None):
            return None
        if (self.hallucinations_schizophrenic
                or self.delusions_schizophrenic
                or self.hallucinations_other
                or self.delusions_other):
            return False
        return True

    def meets_criteria_mania_ignoring_psychosis(self):
        # When can we say "definitely not"?
        if is_false(self.mood_elevated) and is_false(self.mood_irritable):
            return False
        if is_false(self.sustained7days) and is_false(self.admission_required):
            return False
        t = self.count_booleans(Icd10Manic.HYPOMANIA_MANIA_NAMES) + \
            self.count_booleans(Icd10Manic.MANIA_NAMES)
        u = self.n_incomplete(Icd10Manic.HYPOMANIA_MANIA_NAMES) + \
            self.n_incomplete(Icd10Manic.MANIA_NAMES)
        if self.mood_elevated and (t + u < 3):
            # With elevated mood, need at least 3 symptoms
            return False
        if is_false(self.mood_elevated) and (t + u < 4):
            # With only irritable mood, need at least 4 symptoms
            return False
        if is_false(self.severe_interference_functioning):
            return False
        # OK. When can we say "yes"?
        if ((self.mood_elevated or self.mood_irritable)
                and (self.sustained7days or self.admission_required)
                and ((self.mood_elevated and t >= 3)
                     or (self.mood_irritable and t >= 4))
                and self.severe_interference_functioning):
            return True
        return None

    def meets_criteria_hypomania(self):
        # When can we say "definitely not"?
        if self.meets_criteria_mania_ignoring_psychosis():
            return False  # silly to call it hypomania if it's mania
        if is_false(self.mood_elevated) and is_false(self.mood_irritable):
            return False
        if is_false(self.sustained4days):
            return False
        t = self.count_booleans(Icd10Manic.HYPOMANIA_MANIA_NAMES)
        u = self.n_incomplete(Icd10Manic.HYPOMANIA_MANIA_NAMES)
        if t + u < 3:
            # Need at least 3 symptoms
            return False
        if is_false(self.some_interference_functioning):
            return False
        # OK. When can we say "yes"?
        if ((self.mood_elevated or self.mood_irritable)
                and self.sustained4days
                and t >= 3
                and self.some_interference_functioning):
            return True
        return None

    def meets_criteria_none(self):
        h = self.meets_criteria_hypomania()
        m = self.meets_criteria_mania_ignoring_psychosis()
        if h or m:
            return False
        if is_false(h) and is_false(m):
            return True
        return None

    def psychosis_present(self):
        if (self.hallucinations_other
                or self.hallucinations_schizophrenic
                or self.delusions_other
                or self.delusions_schizophrenic):
            return True
        if (self.hallucinations_other is None
                or self.hallucinations_schizophrenic is None
                or self.delusions_other is None
                or self.delusions_schizophrenic is None):
            return None
        return False

    def get_description(self):
        if self.meets_criteria_mania_psychotic_schizophrenic():
            return WSTRING("icd10manic_category_manic_psychotic_schizophrenic")
        elif self.meets_criteria_mania_psychotic_icd():
            return WSTRING("icd10manic_category_manic_psychotic")
        elif self.meets_criteria_mania_nonpsychotic():
            return WSTRING("icd10manic_category_manic_nonpsychotic")
        elif self.meets_criteria_hypomania():
            return WSTRING("icd10manic_category_hypomanic")
        elif self.meets_criteria_none():
            return WSTRING("icd10manic_category_none")
        else:
            return WSTRING("Unknown")

    def is_complete(self):
        return (
            self.date_pertains_to is not None
            and self.meets_criteria_none() is not None
            and self.field_contents_valid()
        )

    def text_row(self, wstringname):
        return heading_spanning_two_columns(WSTRING(wstringname))

    def row_true_false(self, fieldname):
        return self.get_twocol_bool_row_true_false(
            fieldname, WSTRING("icd10manic_" + fieldname))

    def get_task_html(self):
        h = self.get_standard_clinician_block(True, self.comments) + u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa(WSTRING("date_pertains_to"),
                   format_datetime_string(self.date_pertains_to,
                                          DATEFORMAT.LONG_DATE, default=None))
        h += tr_qa(WSTRING("category") + u" <sup>[1,2]</sup>",
                   self.get_description())
        h += tr_qa(WSTRING("icd10manic_psychotic_symptoms")
                   + u" <sup>[2]</sup>",
                   get_present_absent_none(self.psychosis_present()))
        h += u"""
                </table>
            </div>
            <div class="explanation">
        """
        h += WSTRING("icd10_symptomatic_disclaimer")
        h += u"""
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """

        h += self.text_row("icd10manic_core")
        for x in Icd10Manic.CORE_NAMES:
            h += self.row_true_false(x)

        h += self.text_row("icd10manic_hypomania_mania")
        for x in Icd10Manic.HYPOMANIA_MANIA_NAMES:
            h += self.row_true_false(x)

        h += self.text_row("icd10manic_other_mania")
        for x in Icd10Manic.MANIA_NAMES:
            h += self.row_true_false(x)

        h += self.text_row("icd10manic_other_criteria")
        for x in Icd10Manic.OTHER_CRITERIA_NAMES:
            h += self.row_true_false(x)

        h += subheading_spanning_two_columns(WSTRING("icd10manic_psychosis"))
        for x in Icd10Manic.PSYCHOSIS_NAMES:
            h += self.row_true_false(x)

        h += u"""
            </table>
            <div class="footnotes">
                [1] Hypomania:
                    elevated/irritable mood
                    + sustained for ≥4 days
                    + at least 3 of the “other hypomania” symptoms
                    + some interference with functioning.
                Mania:
                    elevated/irritable mood
                    + sustained for ≥7 days or hospital admission required
                    + at least 3 of the “other mania/hypomania” symptoms
                      (4 if mood only irritable)
                    + severe interference with functioning.
                [2] ICD-10 nonpsychotic mania requires mania without
                    hallucinations/delusions.
                ICD-10 psychotic mania requires mania plus
                hallucinations/delusions other than those that are
                “typically schizophrenic”.
                ICD-10 does not clearly categorize mania with only
                schizophreniform psychotic symptoms; however, Schneiderian
                first-rank symptoms can occur in manic psychosis
                (e.g. Conus P et al., 2004, PMID 15337330.).
            </div>
        """ + ICD10_COPYRIGHT_DIV
        return h