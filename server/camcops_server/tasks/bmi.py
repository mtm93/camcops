#!/usr/bin/env python
# bmi.py

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

from typing import List, Optional

import cardinal_pythonlib.rnc_web as ws
from ..cc_modules.cc_html import tr_qa
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    LabelAlignment,
    Task,
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# BMI
# =============================================================================

BMI_DP = 2
KG_DP = 2
M_DP = 3


class Bmi(Task):
    tablename = "bmi"
    shortname = "BMI"
    longname = "Body mass index"
    fieldspecs = [
        dict(name="height_m", cctype="FLOAT", min=0,
             comment="height (m)"),
        dict(name="mass_kg", cctype="FLOAT", min=0,
             comment="mass (kg)"),
        dict(name="comment", cctype="TEXT",
             comment="Clinician's comment"),
    ]

    def is_complete(self) -> bool:
        return (
            self.height_m is not None and
            self.mass_kg is not None and
            self.field_contents_valid()
        )

    def get_trackers(self) -> List[TrackerInfo]:
        # $ signs enable TEX mode for matplotlib, e.g. "$BMI (kg/m^2)$"
        return [
            TrackerInfo(
                value=self.bmi(),
                plot_label="Body mass index",
                axis_label="BMI (kg/m^2)",
                axis_min=10,
                axis_max=42,
                horizontal_lines=[
                    13,
                    15,
                    16,
                    17,
                    17.5,
                    18.5,
                    25,
                    30,
                    35,
                    40
                ],
                horizontal_labels=[
                    # positioned near the mid-range for some:
                    TrackerLabel(12.5, self.wxstring("underweight_under_13"),
                                 LabelAlignment.top),
                    TrackerLabel(14, self.wxstring("underweight_13_15")),
                    TrackerLabel(15.5, self.wxstring("underweight_15_16")),
                    TrackerLabel(16.5, self.wxstring("underweight_16_17")),
                    TrackerLabel(17.25, self.wxstring("underweight_17_17.5")),
                    TrackerLabel(18, self.wxstring("underweight_17.5_18.5")),
                    TrackerLabel(21.75, self.wxstring("normal")),
                    TrackerLabel(27.5, self.wxstring("overweight")),
                    TrackerLabel(32.5, self.wxstring("obese_1")),
                    TrackerLabel(37.6, self.wxstring("obese_2")),
                    TrackerLabel(40.5, self.wxstring("obese_3"),
                                 LabelAlignment.bottom),
                ],
                aspect_ratio=1.0,
            ),
            TrackerInfo(
                value=self.mass_kg,
                plot_label="Mass (kg)",
                axis_label="Mass (kg)"
            ),
        ]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content=(
                "BMI: {} kg⋅m<sup>–2</sup> [{}]. Mass: {} kg. "
                "Height: {} m.".format(
                    ws.number_to_dp(self.bmi(), BMI_DP),
                    self.category(),
                    ws.number_to_dp(self.mass_kg, KG_DP),
                    ws.number_to_dp(self.height_m, M_DP)
                )
            )
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="bmi", cctype="FLOAT",
                 value=self.bmi(), comment="BMI (kg/m^2)"),
        ]

    def bmi(self) -> Optional[float]:
        if not self.is_complete():
            return None
        return self.mass_kg / (self.height_m * self.height_m)

    def category(self) -> str:
        bmi = self.bmi()
        if bmi is None:
            return "?"
        elif bmi >= 40:
            return self.wxstring("obese_3")
        elif bmi >= 35:
            return self.wxstring("obese_2")
        elif bmi >= 30:
            return self.wxstring("obese_1")
        elif bmi >= 25:
            return self.wxstring("overweight")
        elif bmi >= 18.5:
            return self.wxstring("normal")
        elif bmi >= 17.5:
            return self.wxstring("underweight_17.5_18.5")
        elif bmi >= 17:
            return self.wxstring("underweight_17_17.5")
        elif bmi >= 16:
            return self.wxstring("underweight_16_17")
        elif bmi >= 15:
            return self.wxstring("underweight_15_16")
        elif bmi >= 13:
            return self.wxstring("underweight_13_15")
        else:
            return self.wxstring("underweight_under_13")

    def get_task_html(self) -> str:
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr_qa("BMI (kg/m<sup>2</sup>)",
                   ws.number_to_dp(self.bmi(), BMI_DP))
        h += tr_qa("Category <sup>[1]</sup>", self.category())
        h += """
                </table>
            </div>
            <table class="taskdetail">
        """
        h += tr_qa("Mass (kg)", ws.number_to_dp(self.mass_kg, KG_DP))
        h += tr_qa("Height (m)", ws.number_to_dp(self.height_m, M_DP))
        h += tr_qa("Comment", ws.webify(self.comment))
        h += """
            </table>
            <div class="footnotes">
                [1] Categorization <b>for adults</b> (square brackets
                inclusive, parentheses exclusive; AN anorexia nervosa):

                &lt;13 very severely underweight (WHO grade 3; RCPsych severe
                    AN, high risk);
                [13, 15] very severely underweight (WHO grade 3; RCPsych severe
                    AN, medium risk);
                [15, 16) severely underweight (WHO grade 3; AN);
                [16, 17) underweight (WHO grade 2; AN);
                [17, 17.5) underweight (WHO grade 1; below ICD-10/RCPsych AN
                    cutoff);
                [17.5, 18.5) underweight (WHO grade 1);
                [18.5, 25) normal (healthy weight);
                [25, 30) overweight;
                [30, 35) obese class I (moderately obese);
                [35, 40) obese class II (severely obese);
                ≥40 obese class III (very severely obese).

                Sources:
                <ul>
                    <li>WHO Expert Committee on Physical Status (1995,
                    PMID 8594834) defined ranges as:

                    &lt;16 grade 3 thinness,
                    [16, 17) grade 2 thinness,
                    [17, 18.5) grade 1 thinness,
                    [18.5, 25) normal,
                    [25, 30) grade 1 overweight,
                    [30, 40) grade 2 overweight,
                    ≥40 grade 3 overweight

                    (sections 7.2.1 and 8.7.1 and p452).</li>

                    <li>WHO (1998 “Obesity: preventing and managing the global
                    epidemic”) use the
                    categories

                    [25, 30) “pre-obese”,
                    [30, 35) obese class I,
                    [35, 40) obese class II,
                    ≥40 obese class III

                    (p9).</li>

                    <li>A large number of web sources that don’t cite a primary
                    reference use:
                    &lt;15 very severely underweight;
                    [15, 16) severely underweight;
                    [16, 18.5) underweight;
                    [18.5, 25] normal (healthy weight);
                    [25, 30) obese class I (moderately obese);
                    [35, 40) obese class II (severely obese);
                    ≥40 obese class III (very severely obese);

                    <li>The WHO (2010 “Nutrition Landscape Information System
                    (NILS) country profile indicators: interpretation guide”)
                    use
                    &lt;16 “severe thinness” (previously grade 3 thinness),
                    (16, 17] “moderate thinness” (previously grade 2 thinness),
                    [17, 18.5) “underweight” (previously grade 1 thinness).
                    (p3).</li>

                    <li>ICD-10 BMI threshold for anorexia nervosa is ≤17.5
                    (WHO, 1992). Subsequent references (e.g. RCPsych, below)
                    use &lt;17.5.</li>

                    <li>In anorexia nervosa:

                    &lt;17.5 anorexia (threshold for diagnosis),
                    &lt;15 severe anorexia;
                    13–15 medium risk,
                    &lt;13 high risk (of death)

                    (Royal College of Psychiatrists, 2010, report CR162,
                    pp. 11, 15, 20, 56).</li>
                </ul>
            </div>
        """
        return h
