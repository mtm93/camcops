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
from cc_modules.cc_constants import PV
from cc_modules.cc_html import (
    answer,
    get_yes_no_none,
    identity,
    tr,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    STANDARD_TASK_FIELDSPECS,
    STANDARD_ANCILLARY_FIELDSPECS,
    Task,
    Ancillary
)


def a(x):
    """Answer formatting for this task."""
    return answer(x, formatter_answer=identity, default="")


# =============================================================================
# IDED3D
# =============================================================================

class IDED3D_Trial(Ancillary):

    @classmethod
    def get_tablename(cls):
        return "ided3d_trials"

    @classmethod
    def get_fkname(cls):
        return "ided3d_id"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_ANCILLARY_FIELDSPECS + [
            dict(name="ided3d_id", notnull=True,
                 cctype="INT", comment="FK to cardinal_expdet"),
            dict(name="trial", notnull=True, cctype="INT",
                 comment="Trial number (1-based)"),
            dict(name="stage", cctype="INT", comment="Stage number (1-based)"),
            # Locations
            dict(name="correct_location", cctype="INT",
                 comment="Location of correct stimulus "
                         "(0 top, 1 right, 2 bottom, 3 left)"),
            dict(name="incorrect_location", cctype="INT",
                 comment="Location of incorrect stimulus "
                         "(0 top, 1 right, 2 bottom, 3 left)"),
            # Stimuli
            dict(name="correct_shape", cctype="INT",
                 comment="Shape# of correct stimulus"),
            dict(name="correct_colour", cctype="TEXT",
                 comment="HTML colour of correct stimulus"),
            dict(name="correct_number", cctype="INT",
                 comment="Number of copies of correct stimulus"),
            dict(name="incorrect_shape", cctype="INT",
                 comment="Shape# of incorrect stimulus"),
            dict(name="incorrect_colour", cctype="TEXT",
                 comment="HTML colour of incorrect stimulus"),
            dict(name="incorrect_number", cctype="INT",
                 comment="Number of copies of incorrect stimulus"),
            # Trial
            dict(name="trial_start_time", cctype="ISO8601",
                 comment="Trial start time / stimuli presented at (ISO-8601)"),
            # Response
            dict(name="responded", cctype="BOOL", pv=PV.BIT,
                 comment="Trial start time / stimuli presented at (ISO-8601)"),
            dict(name="response_time", cctype="ISO8601",
                 comment="Time of response (ISO-8601)"),
            dict(name="response_latency_ms", cctype="INT",
                 comment="Response latency (ms)"),
            dict(name="correct", cctype="BOOL", pv=PV.BIT,
                 comment="Response was correct"),
            dict(name="incorrect", cctype="BOOL", pv=PV.BIT,
                 comment="Response was incorrect"),
        ]

    @classmethod
    def get_sortfield(self):
        return "trial"

    @classmethod
    def get_html_table_header(cls):
        return u"""
            <table class="extradetail">
                <tr>
                    <th>Trial</th>
                    <th>Stage</th>
                    <th>Correct location</th>
                    <th>Incorrect location</th>
                    <th>Correct shape</th>
                    <th>Correct colour</th>
                    <th>Correct number</th>
                    <th>Incorrect shape</th>
                    <th>Incorrect colour</th>
                    <th>Incorrect number</th>
                    <th>Trial start time</th>
                    <th>Responded?</th>
                    <th>Response time</th>
                    <th>Response latency (ms)</th>
                    <th>Correct?</th>
                    <th>Incorrect?</th>
                </tr>
        """

    def get_html_table_row(self):
        return tr(
            a(self.trial),
            a(self.stage),
            a(self.correct_location),
            a(self.incorrect_location),
            a(self.correct_shape),
            a(self.correct_colour),
            a(self.correct_number),
            a(self.incorrect_shape),
            a(self.incorrect_colour),
            a(self.incorrect_number),
            a(self.trial_start_time),
            a(self.responded),
            a(self.response_time),
            a(self.response_latency_ms),
            a(self.correct),
            a(self.incorrect),
        )


class IDED3D_Stage(Ancillary):

    @classmethod
    def get_tablename(cls):
        return "ided3d_stages"

    @classmethod
    def get_fkname(cls):
        return "ided3d_id"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_ANCILLARY_FIELDSPECS + [
            dict(name="ided3d_id", notnull=True,
                 cctype="INT", comment="FK to cardinal_expdet"),
            dict(name="stage", notnull=True, cctype="INT",
                 comment="Stage number (1-based)"),
            # Config
            dict(name="stage_name", cctype="TEXT",
                 comment="Name of the stage (e.g. SD, EDr)"),
            dict(name="relevant_dimension", cctype="TEXT",
                 comment="Relevant dimension (e.g. shape, colour, number)"),
            dict(name="correct_exemplar", cctype="TEXT",
                 comment="Correct exemplar (from relevant dimension)"),
            dict(name="incorrect_exemplar", cctype="TEXT",
                 comment="Incorrect exemplar (from relevant dimension)"),
            dict(name="correct_stimulus_shapes", cctype="TEXT",
                 comment="Possible shapes for correct stimulus "
                         "(CSV list of shape numbers)"),
            dict(name="correct_stimulus_colours", cctype="TEXT",
                 comment="Possible colours for correct stimulus "
                         "(CSV list of HTML colours)"),
            dict(name="correct_stimulus_numbers", cctype="TEXT",
                 comment="Possible numbers for correct stimulus "
                         "(CSV list of numbers)"),
            dict(name="incorrect_stimulus_shapes", cctype="TEXT",
                 comment="Possible shapes for incorrect stimulus "
                         "(CSV list of shape numbers)"),
            dict(name="incorrect_stimulus_colours", cctype="TEXT",
                 comment="Possible colours for incorrect stimulus "
                         "(CSV list of HTML colours)"),
            dict(name="incorrect_stimulus_numbers", cctype="TEXT",
                 comment="Possible numbers for incorrect stimulus "
                         "(CSV list of numbers)"),
            # Results
            dict(name="first_trial_num", cctype="INT",
                 comment="Number of the first trial of the stage (1-based)"),
            dict(name="n_completed_trials", cctype="INT",
                 comment="Number of trials completed"),
            dict(name="n_correct", cctype="INT",
                 comment="Number of trials performed correctly"),
            dict(name="n_incorrect", cctype="INT",
                 comment="Number of trials performed incorrectly"),
            dict(name="stage_passed", cctype="BOOL", pv=PV.BIT,
                 comment="Subject met criterion and passed stage"),
            dict(name="stage_failed", cctype="BOOL", pv=PV.BIT,
                 comment="Subject took too many trials and failed stage"),
        ]

    @classmethod
    def get_sortfield(self):
        return "stage"

    @classmethod
    def get_html_table_header(cls):
        return u"""
            <table class="extradetail">
                <tr>
                    <th>Stage#</th>
                    <th>Stage name</th>
                    <th>Relevant dimension</th>
                    <th>Correct exemplar</th>
                    <th>Incorrect exemplar</th>
                    <th>Shapes for correct</th>
                    <th>Colours for correct</th>
                    <th>Numbers for correct</th>
                    <th>Shapes for incorrect</th>
                    <th>Colours for incorrect</th>
                    <th>Numbers for incorrect</th>
                    <th>First trial#</th>
                    <th>#completed trials</th>
                    <th>#correct</th>
                    <th>#incorrect</th>
                    <th>Passed?</th>
                    <th>Failed?</th>
                </tr>
        """

    def get_html_table_row(self):
        return tr(
            a(self.stage),
            a(self.stage_name),
            a(self.relevant_dimension),
            a(self.correct_exemplar),
            a(self.incorrect_exemplar),
            a(self.correct_stimulus_shapes),
            a(self.correct_stimulus_colours),
            a(self.correct_stimulus_numbers),
            a(self.incorrect_stimulus_shapes),
            a(self.incorrect_stimulus_colours),
            a(self.incorrect_stimulus_numbers),
            a(self.first_trial_num),
            a(self.n_completed_trials),
            a(self.n_correct),
            a(self.n_incorrect),
            a(self.stage_passed),
            a(self.stage_failed),
        )


class IDED3D(Task):

    @classmethod
    def get_tablename(cls):
        return "ided3d"

    @classmethod
    def get_taskshortname(cls):
        return "ID/ED-3D"

    @classmethod
    def get_tasklongname(cls):
        return u"Three-dimensional ID/ED task"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + [
            # Config
            dict(name="last_stage", cctype="INT",
                 comment="Last stage to offer (1 [SD] - 8 [EDR])"),
            dict(name="max_trials_per_stage", cctype="INT",
                 comment="Maximum number of trials allowed per stage before "
                         "the task aborts"),
            dict(name="progress_criterion_x", cctype="INT",
                 comment='Criterion to proceed to next stage: X correct out of'
                         ' the last Y trials, where this is X'),
            dict(name="progress_criterion_y", cctype="INT",
                 comment='Criterion to proceed to next stage: X correct out of'
                         ' the last Y trials, where this is Y'),
            dict(name="min_number", cctype="INT",
                 comment="Minimum number of stimulus element to use"),
            dict(name="max_number", cctype="INT",
                 comment="Maximum number of stimulus element to use"),
            dict(name="pause_after_beep_ms", cctype="INT",
                 comment="Time to continue visual feedback after auditory "
                         "feedback finished (ms)"),
            dict(name="iti_ms", cctype="INT",
                 comment="Intertrial interval (ms)"),
            dict(name="counterbalance_dimensions", cctype="INT",
                 comment="Dimensional counterbalancing condition (0-5)"),
            dict(name="volume", cctype="FLOAT",
                 comment="Sound volume (0.0-1.0)"),
            dict(name="offer_abort", cctype="BOOL", pv=PV.BIT,
                 comment="Offer an abort button?"),
            dict(name="debug_display_stimuli_only", cctype="BOOL", pv=PV.BIT,
                 comment="DEBUG: show stimuli only, don't run task"),
            # Intrinsic config
            dict(name="shape_definitions_svg", cctype="TEXT",
                 comment="JSON-encoded version of shape definition"
                         " array in SVG format (with arbitrary scale of -60 to"
                         " +60 in both X and Y dimensions)"),
            # Results
            dict(name="aborted", cctype="INT",
                 comment="Was the task aborted? (0 no, 1 yes)"),
            dict(name="finished", cctype="INT",
                 comment="Was the task finished? (0 no, 1 yes)"),
            dict(name="last_trial_completed", cctype="INT",
                 comment="Number of last trial completed"),
        ]

    @classmethod
    def get_dependent_classes(cls):
        return [IDED3D_Trial,
                IDED3D_Stage]

    def is_complete(self):
        return bool(self.finished)

    def get_stage_html(self, stagearray):
        html = IDED3D_Stage.get_html_table_header()
        for s in stagearray:
            html += s.get_html_table_row()
        html += u"""</table>"""
        return html

    def get_trial_html(self, trialarray):
        html = IDED3D_Trial.get_html_table_header()
        for t in trialarray:
            html += t.get_html_table_row()
        html += u"""</table>"""
        return html

    def get_stage_array(self):
        # Fetch group details
        return self.get_ancillary_items(IDED3D_Stage)

    def get_trial_array(self):
        # Fetch trial details
        return self.get_ancillary_items(IDED3D_Trial)

    def get_task_html(self):
        stagearray = self.get_stage_array()
        trialarray = self.get_trial_array()
        # THIS IS A NON-EDITABLE TASK, so we *ignore* the problem
        # of matching to no-longer-current records.
        # (See PhotoSequence.py for a task that does it properly.)

        # Provide HTML
        # HTML
        h = u"""
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <div class="explanation">
                1. Simple discrimination (SD), and 2. reversal (SDr);
                3. compound discrimination (CD), and 4. reversal (CDr);
                5. intradimensional shift (ID), and 6. reversal (IDr);
                7. extradimensional shift (ED), and 8. reversal (EDr).
            </div>
            <table class="taskconfig">
                <tr>
                    <th width="50%">Configuration variable</th>
                    <th width="50%">Value</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
        )
        h += tr_qa(WSTRING("ided3d_last_stage"), self.last_stage)
        h += tr_qa(WSTRING("ided3d_max_trials_per_stage"),
                   self.max_trials_per_stage)
        h += tr_qa(WSTRING("ided3d_progress_criterion_x"),
                   self.progress_criterion_x)
        h += tr_qa(WSTRING("ided3d_progress_criterion_y"),
                   self.progress_criterion_y)
        h += tr_qa(WSTRING("ided3d_min_number"), self.min_number)
        h += tr_qa(WSTRING("ided3d_max_number"), self.max_number)
        h += tr_qa(WSTRING("ided3d_pause_after_beep_ms"),
                   self.pause_after_beep_ms)
        h += tr_qa(WSTRING("ided3d_iti_ms"), self.iti_ms)
        h += tr_qa(WSTRING("ided3d_counterbalance_dimensions")
                   + u"<sup>[1]</sup>",
                   self.counterbalance_dimensions)
        h += tr_qa(WSTRING("volume"), self.volume)
        h += tr_qa(WSTRING("ided3d_offer_abort"), self.offer_abort)
        h += tr_qa(WSTRING("ided3d_debug_display_stimuli_only"),
                   self.debug_display_stimuli_only)
        h += tr_qa(u"Shapes (as a JSON-encoded array of SVG "
                   u"definitions; X and Y range both –60 to +60)",
                   ws.webify(self.shape_definitions_svg))
        h += u"""
            </table>
            <table class="taskdetail">
                <tr><th width="50%">Measure</th><th width="50%">Value</th></tr>
        """
        h += tr_qa("Aborted?", get_yes_no_none(self.aborted))
        h += tr_qa("Finished?", get_yes_no_none(self.finished))
        h += tr_qa("Last trial completed", self.last_trial_completed)
        h += (
            u"""
                </table>
                <div>Stage specifications and results:</div>
            """
            + self.get_stage_html(stagearray)
            + u"<div>Trial-by-trial results:</div>"
            + self.get_trial_html(trialarray)
            + u"""
                <div class="footnotes">
                    [1] Counterbalancing of dimensions is as follows, with
                    notation X/Y indicating that X is the first relevant
                    dimension (for stages SD–IDr) and Y is the second relevant
                    dimension (for stages ED–EDr).
                    0: shape/colour.
                    1: colour/number.
                    2: number/shape.
                    3: shape/number.
                    4: colour/shape.
                    5: number/colour.
                </div>
            """
        )
        return h