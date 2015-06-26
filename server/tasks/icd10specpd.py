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
from cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from cc_modules.cc_dt import format_datetime_string
from cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    get_yes_no_unknown,
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
# Icd10SpecPD
# =============================================================================

def ctv_dict_pd(condition, has_it):
    return {"content": condition + ": " + get_yes_no_unknown(has_it)}


class Icd10SpecPD(Task):
    N_GENERAL = 6
    N_GENERAL_1 = 4
    N_PARANOID = 7
    N_SCHIZOID = 9
    N_DISSOCIAL = 6
    N_EU = 10
    N_EUPD_I = 5
    N_HISTRIONIC = 6
    N_ANANKASTIC = 8
    N_ANXIOUS = 5
    N_DEPENDENT = 6
    TASK_FIELDSPECS = (
        CLINICIAN_FIELDSPECS
        + [
            dict(name="date_pertains_to", cctype="ISO8601",
                 comment="Date the assessment pertains to"),
            dict(name="comments", cctype="TEXT",
                 comment="Clinician's comments"),
            dict(name="skip_paranoid", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for paranoid PD?"),
            dict(name="skip_schizoid", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for schizoid PD?"),
            dict(name="skip_dissocial", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for dissocial PD?"),
            dict(name="skip_eu", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for emotionally unstable PD?"),
            dict(name="skip_histrionic", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for histrionic PD?"),
            dict(name="skip_anankastic", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for anankastic PD?"),
            dict(name="skip_anxious", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for anxious PD?"),
            dict(name="skip_dependent", cctype="BOOL", pv=PV.BIT,
                 comment="Skip questions for dependent PD?"),
            dict(name="vignette", cctype="TEXT", pv=PV.BIT,
                 comment="Vignette"),
        ]
        + repeat_fieldspec(
            "g", 1, N_GENERAL, "BOOL", pv=PV.BIT,
            comment_fmt="G{n}: {s}",
            comment_strings=["pathological 1", "pervasive",
                             "pathological 2", "persistent",
                             "primary 1", "primary 2"])
        + repeat_fieldspec(
            "g1_", 1, N_GENERAL_1, "BOOL", pv=PV.BIT,
            comment_fmt="G1{n}: {s}",
            comment_strings=["cognition", "affectivity",
                             "impulse control", "interpersonal"])
        + repeat_fieldspec(
            "paranoid", 1, N_PARANOID, "BOOL", pv=PV.BIT,
            comment_fmt="Paranoid ({n}): {s}",
            comment_strings=["sensitive", "grudges", "suspicious",
                             "personal rights", "sexual jealousy",
                             "self-referential", "conspiratorial"])
        + repeat_fieldspec(
            "schizoid", 1, N_SCHIZOID, "BOOL", pv=PV.BIT,
            comment_fmt="Schizoid ({n}): {s}",
            comment_strings=["little pleasure",
                             "cold/detached",
                             "limited capacity for warmth",
                             "indifferent to praise/criticism",
                             "little interest in sex",
                             "solitary",
                             "fantasy/introspection",
                             "0/1 close friends/confidants",
                             "insensitive to social norms"])
        + repeat_fieldspec(
            "dissocial", 1, N_DISSOCIAL, "BOOL", pv=PV.BIT,
            comment_fmt="Dissocial ({n}): {s}",
            comment_strings=["unconcern", "irresponsibility",
                             "incapacity to maintain relationships",
                             "low tolerance to frustration",
                             "incapacity for guilt",
                             "prone to blame others"])
        + repeat_fieldspec(
            "eu", 1, N_EU, "BOOL", pv=PV.BIT,
            comment_fmt="Emotionally unstable ({n}): {s}",
            comment_strings=["act without considering consequences",
                             "quarrelsome", "outbursts of anger",
                             "can't maintain actions with immediate reward",
                             "unstable/capricious mood",
                             "uncertain self-image",
                             "intense/unstable relationships",
                             "avoids abandonment",
                             "threats/acts of self-harm",
                             "feelings of emptiness"])
        + repeat_fieldspec(
            "histrionic", 1, N_HISTRIONIC, "BOOL", pv=PV.BIT,
            comment_fmt="Histrionic ({n}): {s}",
            comment_strings=["theatricality",
                             "suggestibility",
                             "shallow/labile affect",
                             "centre of attention",
                             "inappropriately seductive",
                             "concerned with attractivness"])
        + repeat_fieldspec(
            "anankastic", 1, N_ANANKASTIC, "BOOL", pv=PV.BIT,
            comment_fmt="Anankastic ({n}): {s}",
            comment_strings=["doubt/caution",
                             "preoccupation with details",
                             "perfectionism",
                             "excessively conscientious",
                             "preoccupied with productivity",
                             "excessive pedantry",
                             "rigid/stubborn",
                             "require others do things specific way"])
        + repeat_fieldspec(
            "anxious", 1, N_ANXIOUS, "BOOL", pv=PV.BIT,
            comment_fmt="Anxious ({n}), {s}",
            comment_strings=["tension/apprehension",
                             "preoccupied with criticism/rejection",
                             "won't get involved unless certain liked",
                             "need for security restricts lifestyle",
                             "avoidance of interpersonal contact"])
        + repeat_fieldspec(
            "dependent", 1, N_DEPENDENT, "BOOL", pv=PV.BIT,
            comment_fmt="Dependent ({n}): {s}",
            comment_strings=["others decide",
                             "subordinate needs to those of others",
                             "unwilling to make reasonable demands",
                             "uncomfortable/helpless when alone",
                             "fears of being left to oneself",
                             "everyday decisions require advice/reassurance"])
    )

    @classmethod
    def get_tablename(cls):
        return "icd10specpd"

    @classmethod
    def get_taskshortname(cls):
        return "ICD10-PD"

    @classmethod
    def get_tasklongname(cls):
        return u"ICD-10 criteria for specific personality disorders (F60)"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + Icd10SpecPD.TASK_FIELDSPECS

    def get_clinical_text(self):
        if not self.is_complete():
            return CTV_DICTLIST_INCOMPLETE
        dl = []
        dl.append(ctv_dict_pd(WSTRING("icd10pd_meets_general_criteria"),
                              self.hasPD()))
        dl.append(ctv_dict_pd(WSTRING("icd10_paranoid_pd_title"),
                              self.hasParanoidPD()))
        dl.append(ctv_dict_pd(WSTRING("icd10_schizoid_pd_title"),
                              self.hasSchizoidPD()))
        dl.append(ctv_dict_pd(WSTRING("icd10_dissocial_pd_title"),
                              self.hasDissocialPD()))
        dl.append(ctv_dict_pd(WSTRING("icd10_eu_pd_i_title"),
                              self.hasEUPD_I()))
        dl.append(ctv_dict_pd(WSTRING("icd10_eu_pd_b_title"),
                              self.hasEUPD_B()))
        dl.append(ctv_dict_pd(WSTRING("icd10_histrionic_pd_title"),
                              self.hasHistrionicPD()))
        dl.append(ctv_dict_pd(WSTRING("icd10_anankastic_pd_title"),
                              self.hasAnankasticPD()))
        dl.append(ctv_dict_pd(WSTRING("icd10_anxious_pd_title"),
                              self.hasAnxiousPD()))
        dl.append(ctv_dict_pd(WSTRING("icd10_dependent_pd_title"),
                              self.hasDependentPD()))
        return dl

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="meets_general_criteria", cctype="BOOL",
                 value=self.hasPD(),
                 comment="Meets general criteria for personality disorder?"),
            dict(name="paranoid_pd", cctype="BOOL",
                 value=self.hasParanoidPD(),
                 comment="Meets criteria for paranoid PD?"),
            dict(name="schizoid_pd", cctype="BOOL",
                 value=self.hasSchizoidPD(),
                 comment="Meets criteria for schizoid PD?"),
            dict(name="dissocial_pd", cctype="BOOL",
                 value=self.hasDissocialPD(),
                 comment="Meets criteria for dissocial PD?"),
            dict(name="eupd_i", cctype="BOOL",
                 value=self.hasEUPD_I(),
                 comment="Meets criteria for EUPD (impulsive type)?"),
            dict(name="eupd_b", cctype="BOOL",
                 value=self.hasEUPD_B(),
                 comment="Meets criteria for EUPD (borderline type)?"),
            dict(name="histrionic_pd", cctype="BOOL",
                 value=self.hasHistrionicPD(),
                 comment="Meets criteria for histrionic PD?"),
            dict(name="anankastic_pd", cctype="BOOL",
                 value=self.hasAnankasticPD(),
                 comment="Meets criteria for anankastic PD?"),
            dict(name="anxious_pd", cctype="BOOL",
                 value=self.hasAnxiousPD(),
                 comment="Meets criteria for anxious PD?"),
            dict(name="dependent_pd", cctype="BOOL",
                 value=self.hasDependentPD(),
                 comment="Meets criteria for dependent PD?"),
        ]

    def isPDExcluded(self):
        return (
            is_false(self.g1)
            or is_false(self.g2)
            or is_false(self.g3)
            or is_false(self.g4)
            or is_false(self.g5)
            or is_false(self.g6)
            or (
                self.are_all_fields_complete(
                    repeat_fieldname("g1_", 1, Icd10SpecPD.N_GENERAL_1))
                and self.count_booleans(
                    repeat_fieldname("g1_", 1, Icd10SpecPD.N_GENERAL_1)) <= 1
            )
        )

    def isCompleteGeneral(self):
        return (
            self.are_all_fields_complete(
                repeat_fieldname("g", 1, Icd10SpecPD.N_GENERAL))
            and self.are_all_fields_complete(
                repeat_fieldname("g1_", 1, Icd10SpecPD.N_GENERAL_1))
        )

    def isCompleteParanoid(self):
        return self.are_all_fields_complete(
            repeat_fieldname("paranoid", 1, Icd10SpecPD.N_PARANOID))

    def isCompleteSchizoid(self):
        return self.are_all_fields_complete(
            repeat_fieldname("schizoid", 1, Icd10SpecPD.N_SCHIZOID))

    def isCompleteDissocial(self):
        return self.are_all_fields_complete(
            repeat_fieldname("dissocial", 1, Icd10SpecPD.N_DISSOCIAL))

    def isCompleteEU(self):
        return self.are_all_fields_complete(
            repeat_fieldname("eu", 1, Icd10SpecPD.N_EU))

    def isCompleteHistrionic(self):
        return self.are_all_fields_complete(
            repeat_fieldname("histrionic", 1, Icd10SpecPD.N_HISTRIONIC))

    def isCompleteAnankastic(self):
        return self.are_all_fields_complete(
            repeat_fieldname("anankastic", 1, Icd10SpecPD.N_ANANKASTIC))

    def isCompleteAnxious(self):
        return self.are_all_fields_complete(
            repeat_fieldname("anxious", 1, Icd10SpecPD.N_ANXIOUS))

    def isCompleteDependent(self):
        return self.are_all_fields_complete(
            repeat_fieldname("dependent", 1, Icd10SpecPD.N_DEPENDENT))

    # Meets criteria? These also return null for unknown.
    def hasPD(self):
        if self.isPDExcluded():
            return False
        if not self.isCompleteGeneral():
            return None
        return (
            self.all_true(repeat_fieldname("g", 1, Icd10SpecPD.N_GENERAL))
            and self.count_booleans(
                repeat_fieldname("g1_", 1, Icd10SpecPD.N_GENERAL_1)) > 1
        )

    def hasParanoidPD(self):
        if not self.hasPD():
            return self.hasPD()
        if not self.isCompleteParanoid():
            return None
        return (self.count_booleans(
            repeat_fieldname("paranoid", 1, Icd10SpecPD.N_PARANOID)) >= 4)

    def hasSchizoidPD(self):
        if not self.hasPD():
            return self.hasPD()
        if not self.isCompleteSchizoid():
            return None
        return (self.count_booleans(
            repeat_fieldname("schizoid", 1, Icd10SpecPD.N_SCHIZOID)) >= 4)

    def hasDissocialPD(self):
        if not self.hasPD():
            return self.hasPD()
        if not self.isCompleteDissocial():
            return None
        return (self.count_booleans(
            repeat_fieldname("dissocial", 1, Icd10SpecPD.N_DISSOCIAL)) >= 3)

    def hasEUPD_I(self):
        if not self.hasPD():
            return self.hasPD()
        if not self.isCompleteEU():
            return None
        return (
            self.count_booleans(
                repeat_fieldname("eu", 1, Icd10SpecPD.N_EUPD_I)) >= 3
            and self.eu2
        )

    def hasEUPD_B(self):
        if not self.hasPD():
            return self.hasPD()
        if not self.isCompleteEU():
            return None
        return (
            self.count_booleans(
                repeat_fieldname("eu", 1, Icd10SpecPD.N_EUPD_I)) >= 3
            and self.count_booleans(
                repeat_fieldname("eu",
                                 Icd10SpecPD.N_EUPD_I + 1,
                                 Icd10SpecPD.N_EU)) >= 2
        )

    def hasHistrionicPD(self):
        if not self.hasPD():
            return self.hasPD()
        if not self.isCompleteHistrionic():
            return None
        return (self.count_booleans(
            repeat_fieldname("histrionic", 1, Icd10SpecPD.N_HISTRIONIC)) >= 4)

    def hasAnankasticPD(self):
        if not self.hasPD():
            return self.hasPD()
        if not self.isCompleteAnankastic():
            return None
        return (self.count_booleans(
            repeat_fieldname("anankastic", 1, Icd10SpecPD.N_ANANKASTIC)) >= 4)

    def hasAnxiousPD(self):
        if not self.hasPD():
            return self.hasPD()
        if not self.isCompleteAnxious():
            return None
        return (self.count_booleans(
            repeat_fieldname("anxious", 1, Icd10SpecPD.N_ANXIOUS)) >= 4)

    def hasDependentPD(self):
        if not self.hasPD():
            return self.hasPD()
        if not self.isCompleteDependent():
            return None
        return (self.count_booleans(
            repeat_fieldname("dependent", 1, Icd10SpecPD.N_DEPENDENT)) >= 4)

    def is_complete(self):
        return (
            self.date_pertains_to is not None
            and (
                self.isPDExcluded() or (
                    self.isCompleteGeneral()
                    and (self.skip_paranoid or self.isCompleteParanoid())
                    and (self.skip_schizoid or self.isCompleteSchizoid())
                    and (self.skip_dissocial or self.isCompleteDissocial())
                    and (self.skip_eu or self.isCompleteEU())
                    and (self.skip_histrionic or self.isCompleteHistrionic())
                    and (self.skip_anankastic or self.isCompleteAnankastic())
                    and (self.skip_anxious or self.isCompleteAnxious())
                    and (self.skip_dependent or self.isCompleteDependent())
                )
            )
            and self.field_contents_valid()
        )

    def pd_heading(self, wstringname):
        return u"""
            <tr class="heading"><td colspan="2">{}</td></tr>
        """.format(WSTRING(wstringname))

    def pd_skiprow(self, stem):
        return self.get_twocol_bool_row("skip_" + stem,
                                        label=WSTRING("icd10pd_skip_this_pd"))

    def pd_subheading(self, wstringname):
        return u"""
            <tr class="subheading"><td colspan="2">{}</td></tr>
        """.format(WSTRING(wstringname))

    def pd_general_criteria_bits(self):
        return """
            <tr><td>{}</td><td><i><b>{}</b></i></td></tr>
        """.format(
            WSTRING("icd10pd_general_criteria_must_be_met"),
            get_yes_no_unknown(self.hasPD())
        )

    def pd_b_text(self, wstringname):
        return u"""
            <tr><td>{}</td><td class="subheading"></td></tr>
        """.format(WSTRING(wstringname))

    def pd_basic_row(self, stem, i):
        return self.get_twocol_bool_row_true_false(
            stem + str(i), WSTRING("icd10_" + stem + "_pd_" + str(i)))

    def standard_pd_html(self, stem, n):
        html = self.pd_heading("icd10_" + stem + "_pd_title")
        html += self.pd_skiprow(stem)
        html += self.pd_general_criteria_bits()
        html += self.pd_b_text("icd10_" + stem + "_pd_B")
        for i in range(1, n + 1):
            html += self.pd_basic_row(stem, i)
        return html

    def get_task_html(self):
        h = self.get_standard_clinician_block(True, self.comments) + u"""
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr_qa(WSTRING("date_pertains_to"),
                   format_datetime_string(self.date_pertains_to,
                                          DATEFORMAT.LONG_DATE, default=None))
        h += tr_qa(WSTRING("icd10pd_meets_general_criteria"),
                   get_yes_no_none(self.hasPD()))
        h += tr_qa(WSTRING("icd10_paranoid_pd_title"),
                   get_yes_no_none(self.hasParanoidPD()))
        h += tr_qa(WSTRING("icd10_schizoid_pd_title"),
                   get_yes_no_none(self.hasSchizoidPD()))
        h += tr_qa(WSTRING("icd10_dissocial_pd_title"),
                   get_yes_no_none(self.hasDissocialPD()))
        h += tr_qa(WSTRING("icd10_eu_pd_i_title"),
                   get_yes_no_none(self.hasEUPD_I()))
        h += tr_qa(WSTRING("icd10_eu_pd_b_title"),
                   get_yes_no_none(self.hasEUPD_B()))
        h += tr_qa(WSTRING("icd10_histrionic_pd_title"),
                   get_yes_no_none(self.hasHistrionicPD()))
        h += tr_qa(WSTRING("icd10_anankastic_pd_title"),
                   get_yes_no_none(self.hasAnankasticPD()))
        h += tr_qa(WSTRING("icd10_anxious_pd_title"),
                   get_yes_no_none(self.hasAnxiousPD()))
        h += tr_qa(WSTRING("icd10_dependent_pd_title"),
                   get_yes_no_none(self.hasDependentPD()))

        h += u"""
                </table>
            </div>
            <div>
                <p><i>Vignette:</i></p>
                <p>{}</p>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """.format(
            answer(ws.webify(self.vignette), default_for_blank_strings=True)
        )

        # General
        h += subheading_spanning_two_columns(WSTRING("icd10pd_general"))
        h += self.get_twocol_bool_row_true_false("g1", WSTRING("icd10pd_G1"))
        h += self.pd_b_text("icd10pd_G1b")
        for i in range(1, Icd10SpecPD.N_GENERAL_1 + 1):
            h += self.get_twocol_bool_row_true_false(
                "g1_" + str(i), WSTRING("icd10pd_G1_" + str(i)))
        for i in range(2, Icd10SpecPD.N_GENERAL + 1):
            h += self.get_twocol_bool_row_true_false(
                "g" + str(i), WSTRING("icd10pd_G" + str(i)))

        # Paranoid, etc.
        h += self.standard_pd_html("paranoid", Icd10SpecPD.N_PARANOID)
        h += self.standard_pd_html("schizoid", Icd10SpecPD.N_SCHIZOID)
        h += self.standard_pd_html("dissocial", Icd10SpecPD.N_DISSOCIAL)

        # EUPD is special
        h += self.pd_heading("icd10_eu_pd_title")
        h += self.pd_skiprow("eu")
        h += self.pd_general_criteria_bits()
        h += self.pd_subheading("icd10_eu_pd_i_title")
        h += self.pd_b_text("icd10_eu_pd_i_B")
        for i in range(1, Icd10SpecPD.N_EUPD_I + 1):
            h += self.pd_basic_row("eu", i)
        h += self.pd_subheading("icd10_eu_pd_b_title")
        h += self.pd_b_text("icd10_eu_pd_b_B")
        for i in range(Icd10SpecPD.N_EUPD_I + 1, Icd10SpecPD.N_EU + 1):
            h += self.pd_basic_row("eu", i)

        # Back to plain ones
        h += self.standard_pd_html("histrionic", Icd10SpecPD.N_HISTRIONIC)
        h += self.standard_pd_html("anankastic", Icd10SpecPD.N_ANANKASTIC)
        h += self.standard_pd_html("anxious", Icd10SpecPD.N_ANXIOUS)
        h += self.standard_pd_html("dependent", Icd10SpecPD.N_DEPENDENT)

        # Done
        h += u"""
            </table>
        """ + ICD10_COPYRIGHT_DIV
        return h