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

import math
import matplotlib.pyplot as plt
import numpy

import pythonlib.rnc_plot as rnc_plot
import pythonlib.rnc_web as ws

from cc_modules.cc_html import (
    get_html_from_pyplot_figure,
    get_yes_no_none,
    tr_qa,
)
from cc_modules.cc_string import WSTRING
from cc_modules.cc_task import (
    FULLWIDTH_PLOT_WIDTH,
    STANDARD_TASK_FIELDSPECS,
    STANDARD_ANCILLARY_FIELDSPECS,
    Task,
    Ancillary
)


LOWER_MARKER = 0.25
UPPER_MARKER = 0.75
EQUATION_COMMENT = (
    "logits: L(X) = intercept + slope * X; "
    "probability: P = 1 / (1 + exp(-intercept - slope * X))"
)
MODALITY_AUDITORY = 0
MODALITY_VISUAL = 1
DP = 3


# =============================================================================
# Cardinal_ExpDetThreshold
# =============================================================================

class Cardinal_ExpDetThreshold_Trial(Ancillary):

    @classmethod
    def get_tablename(cls):
        return "cardinal_expdetthreshold_trials"

    @classmethod
    def get_fkname(cls):
        return "cardinal_expdetthreshold_id"

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_ANCILLARY_FIELDSPECS + [
            dict(name="cardinal_expdetthreshold_id", notnull=True,
                 cctype="INT",
                 comment="FK to cardinal_expdetthreshold"),
            dict(name="trial", notnull=True, cctype="INT",
                 comment="Trial number"),
            # Results
            dict(name="trial_ignoring_catch_trials", cctype="INT",
                 comment="Trial number, ignoring catch trials"),
            dict(name="target_presented", cctype="INT",
                 comment="Target presented? (0 no, 1 yes)"),
            dict(name="target_time", cctype="ISO8601",
                 comment="Target presentation time (ISO-8601)"),
            dict(name="intensity", cctype="FLOAT",
                 comment="Target intensity (0.0-1.0)"),
            dict(name="choice_time", cctype="ISO8601",
                 comment="Time choice offered (ISO-8601)"),
            dict(name="responded", cctype="INT",
                 comment="Responded? (0 no, 1 yes)"),
            dict(name="response_time", cctype="ISO8601",
                 comment="Time of response (ISO-8601)"),
            dict(name="response_latency_ms", cctype="INT",
                 comment="Response latency (ms)"),
            dict(name="yes", cctype="INT",
                 comment="Subject chose YES? (0 didn't, 1 did)"),
            dict(name="no", cctype="INT",
                 comment="Subject chose NO? (0 didn't, 1 did)"),
            dict(name="caught_out_reset", cctype="INT",
                 comment="Caught out on catch trial, thus reset? (0 no, "
                 "1 yes)"),
            dict(name="trial_num_in_calculation_sequence", cctype="INT",
                 comment="Trial number as used for threshold calculation"),
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
                    <th>Trial (ignoring catch trials)</th>
                    <th>Target presented?</th>
                    <th>Target time</th>
                    <th>Intensity</th>
                    <th>Choice time</th>
                    <th>Responded?</th>
                    <th>Response time</th>
                    <th>Response latency (ms)</th>
                    <th>Yes?</th>
                    <th>No?</th>
                    <th>Caught out (and reset)?</th>
                    <th>Trial# in calculation sequence</th>
                </tr>
        """

    def get_html_table_row(self):
        return (u"<tr>" + u"<td>{}</td>" * 13 + u"</th>").format(
            self.trial,
            self.trial_ignoring_catch_trials,
            self.target_presented,
            self.target_time,
            ws.number_to_dp(self.intensity, DP),
            self.choice_time,
            self.responded,
            self.response_time,
            self.response_latency_ms,
            self.yes,
            self.no,
            ws.webify(self.caught_out_reset),
            ws.webify(self.trial_num_in_calculation_sequence)
        )


class Cardinal_ExpDetThreshold(Task):
    @classmethod
    def get_tablename(cls):
        return "cardinal_expdetthreshold"

    @classmethod
    def get_taskshortname(cls):
        return "Cardinal_ExpDetThreshold"

    @classmethod
    def get_tasklongname(cls):
        return (u"Cardinal RN – Threshold determination for "
                u"Expectation–Detection task")

    @classmethod
    def get_fieldspecs(cls):
        return STANDARD_TASK_FIELDSPECS + [
            # Config
            dict(name="modality", cctype="INT",
                 comment="Modality (0 auditory, 1 visual)"),
            dict(name="target_number", cctype="INT",
                 comment="Target number (within available targets of that "
                 "modality)"),
            dict(name="background_filename", cctype="TEXT",
                 comment="Filename of media used for background"),
            dict(name="target_filename", cctype="TEXT",
                 comment="Filename of media used for target"),
            dict(name="visual_target_duration_s", cctype="FLOAT",
                 comment="Visual target duration (s)"),
            dict(name="background_intensity", cctype="FLOAT",
                 comment="Intensity of background (0.0-1.0)"),
            dict(name="start_intensity_min", cctype="FLOAT",
                 comment="Minimum starting intensity (0.0-1.0)"),
            dict(name="start_intensity_max", cctype="FLOAT",
                 comment="Maximum starting intensity (0.0-1.0)"),
            dict(name="initial_large_intensity_step", cctype="FLOAT",
                 comment="Initial, large, intensity step (0.0-1.0)"),
            dict(name="main_small_intensity_step", cctype="FLOAT",
                 comment="Main, small, intensity step (0.0-1.0)"),
            dict(name="num_trials_in_main_sequence", cctype="INT",
                 comment="Number of trials required in main sequence"),
            dict(name="p_catch_trial", cctype="FLOAT",
                 comment="Probability of catch trial"),
            dict(name="prompt", cctype="TEXT",
                 comment="Prompt given to subject"),
            dict(name="iti_s", cctype="FLOAT",
                 comment="Intertrial interval (s)"),
            # Results
            dict(name="finished", cctype="INT",
                 comment="Subject finished successfully (0 no, 1 yes)"),
            dict(name="intercept", cctype="FLOAT",
                 comment=EQUATION_COMMENT),
            dict(name="slope", cctype="FLOAT",
                 comment=EQUATION_COMMENT),
            dict(name="k", cctype="FLOAT",
                 comment=EQUATION_COMMENT + "; k = slope"),
            dict(name="theta", cctype="FLOAT",
                 comment=EQUATION_COMMENT +
                 "; theta = -intercept/k = -intercept/slope "),
        ]

    @classmethod
    def get_dependent_classes(cls):
        return [Cardinal_ExpDetThreshold_Trial]

    @classmethod
    def use_landscape_for_pdf(self):
        return True

    def is_complete(self):
        return bool(self.finished)

    def get_trial_array(self):
        return self.get_ancillary_items(Cardinal_ExpDetThreshold_Trial)

    def get_trial_html(self):

        # Fetch trial details
        trialarray = self.get_trial_array()

        # Provide HTML
        html = Cardinal_ExpDetThreshold_Trial.get_html_table_header()
        for t in trialarray:
            html += t.get_html_table_row()
        html += u"""</table>"""

        # Don't add figures if we're incomplete
        if not self.is_complete():
            return html

        # Add figures

        FIGSIZE = (FULLWIDTH_PLOT_WIDTH/2, FULLWIDTH_PLOT_WIDTH/2)
        JITTER_STEP = 0.02
        DP_TO_CONSIDER_SAME_FOR_JITTER = 3
        Y_EXTRA_SPACE = 0.1
        X_EXTRA_SPACE = 0.02
        trialfig = plt.figure(figsize=FIGSIZE)
        notcalc_detected_x = []
        notcalc_detected_y = []
        notcalc_missed_x = []
        notcalc_missed_y = []
        calc_detected_x = []
        calc_detected_y = []
        calc_missed_x = []
        calc_missed_y = []
        catch_detected_x = []
        catch_detected_y = []
        catch_missed_x = []
        catch_missed_y = []
        all_x = []
        all_y = []
        for t in trialarray:
            x = t.trial
            y = t.intensity
            all_x.append(x)
            all_y.append(y)
            if t.trial_num_in_calculation_sequence is not None:
                if t.yes:
                    calc_detected_x.append(x)
                    calc_detected_y.append(y)
                else:
                    calc_missed_x.append(x)
                    calc_missed_y.append(y)
            elif t.target_presented:
                if t.yes:
                    notcalc_detected_x.append(x)
                    notcalc_detected_y.append(y)
                else:
                    notcalc_missed_x.append(x)
                    notcalc_missed_y.append(y)
            else:  # catch trial
                if t.yes:
                    catch_detected_x.append(x)
                    catch_detected_y.append(y)
                else:
                    catch_missed_x.append(x)
                    catch_missed_y.append(y)
        plt.plot(all_x,              all_y,              marker="",
                 color="0.9", linestyle="-", label=None)
        plt.plot(notcalc_missed_x,   notcalc_missed_y,   marker="o",
                 color="k",   linestyle="None", label="miss")
        plt.plot(notcalc_detected_x, notcalc_detected_y, marker="+",
                 color="k",   linestyle="None", label="hit")
        plt.plot(calc_missed_x,      calc_missed_y,      marker="o",
                 color="r",   linestyle="None", label="miss, scored")
        plt.plot(calc_detected_x,    calc_detected_y,    marker="+",
                 color="b",   linestyle="None", label="hit, scored")
        plt.plot(catch_missed_x,     catch_missed_y,     marker="o",
                 color="w",   linestyle="None", label="CR")
        plt.plot(catch_detected_x,   catch_detected_y,   marker="*",
                 color="w",   linestyle="None", label="FA")
        leg = plt.legend(
            numpoints=1,
            fancybox=True,  # for set_alpha (below)
            loc="best",  # bbox_to_anchor=(0.75, 1.05)
            labelspacing=0,
            handletextpad=0
        )
        leg.get_frame().set_alpha(0.5)
        plt.xlabel("Trial number")
        plt.ylabel("Intensity")
        plt.ylim(0 - Y_EXTRA_SPACE, 1 + Y_EXTRA_SPACE)
        plt.xlim(-0.5, len(trialarray) - 0.5)

        fitfig = None
        if self.k is not None and self.theta is not None:
            fitfig = plt.figure(figsize=FIGSIZE)
            detected_x = []
            detected_x_approx = []
            detected_y = []
            missed_x = []
            missed_x_approx = []
            missed_y = []
            all_x = []
            for t in trialarray:
                if t.trial_num_in_calculation_sequence is not None:
                    all_x.append(t.intensity)
                    approx_x = "{0:.{precision}f}".format(
                        t.intensity,
                        precision=DP_TO_CONSIDER_SAME_FOR_JITTER
                    )
                    if t.yes:
                        detected_y.append(1 - detected_x_approx.count(approx_x)
                                          * JITTER_STEP)
                        detected_x.append(t.intensity)
                        detected_x_approx.append(approx_x)
                    else:
                        missed_y.append(0 + missed_x_approx.count(approx_x)
                                        * JITTER_STEP)
                        missed_x.append(t.intensity)
                        missed_x_approx.append(approx_x)
            fit_x = numpy.arange(0.0 - X_EXTRA_SPACE, 1.0 + X_EXTRA_SPACE,
                                 0.001)
            fit_y = rnc_plot.logistic(fit_x, self.k, self.theta)
            plt.plot(fit_x,      fit_y,
                     color="g", linestyle="-")
            plt.plot(missed_x,   missed_y,   marker="o",
                     color="r", linestyle="None")
            plt.plot(detected_x, detected_y, marker="+",
                     color="b", linestyle="None")
            plt.ylim(0 - Y_EXTRA_SPACE, 1 + Y_EXTRA_SPACE)
            plt.xlim(numpy.amin(all_x) - X_EXTRA_SPACE,
                     numpy.amax(all_x) + X_EXTRA_SPACE)
            marker_points = []
            for y in (LOWER_MARKER, 0.5, UPPER_MARKER):
                x = rnc_plot.inv_logistic(y, self.k, self.theta)
                marker_points.append((x, y))
            for p in marker_points:
                plt.plot([p[0], p[0]], [-1, p[1]], color="0.5", linestyle=":")
                plt.plot([-1, p[0]], [p[1], p[1]], color="0.5", linestyle=":")
            plt.xlabel("Intensity")
            plt.ylabel("Detected? (0=no, 1=yes; jittered)")

        html += u"""
            <table class="noborder">
                <tr>
                    <td class="noborderphoto">{}</td>
                    <td class="noborderphoto">{}</td>
                </tr>
            </table>
        """.format(
            get_html_from_pyplot_figure(trialfig),
            get_html_from_pyplot_figure(fitfig)
        )

        return html

    def logistic_x_from_p(self, p):
        try:
            return (math.log(p / (1 - p)) - self.intercept) / self.slope
        except (TypeError, ValueError):
            return None

    def get_task_html(self):
        if self.modality == MODALITY_AUDITORY:
            modality = WSTRING("auditory")
        elif self.modality == MODALITY_VISUAL:
            modality = WSTRING("visual")
        else:
            modality = None
        h = u"""
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <div class="explanation">
                The ExpDet-Threshold task measures visual and auditory
                thresholds for stimuli on a noisy background, using a
                single-interval up/down method. It is intended as a prequel to
                the Expectation–Detection task.
            </div>
            <table class="taskconfig">
                <tr>
                    <th width="50%">Configuration variable</th>
                    <th width="50%">Value</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
        )
        h += tr_qa("Modality", modality)
        h += tr_qa("Target number", self.target_number)
        h += tr_qa("Background filename", ws.webify(self.background_filename))
        h += tr_qa("Background intensity", self.background_intensity)
        h += tr_qa("Target filename", ws.webify(self.target_filename))
        h += tr_qa("(For visual targets) Target duration (s)",
                   self.visual_target_duration_s)
        h += tr_qa("Start intensity (minimum)", self.start_intensity_min)
        h += tr_qa("Start intensity (maximum)", self.start_intensity_max)
        h += tr_qa("Initial (large) intensity step",
                   self.initial_large_intensity_step)
        h += tr_qa("Main (small) intensity step",
                   self.main_small_intensity_step)
        h += tr_qa("Number of trials in main sequence",
                   self.num_trials_in_main_sequence)
        h += tr_qa("Probability of a catch trial", self.p_catch_trial)
        h += tr_qa("Prompt", self.prompt)
        h += tr_qa("Intertrial interval (ITI) (s)", self.iti_s)
        h += u"""
            </table>
            <table class="taskdetail">
                <tr><th width="50%">Measure</th><th width="50%">Value</th></tr>
        """
        h += tr_qa("Finished?", get_yes_no_none(self.finished))
        h += tr_qa("Logistic intercept",
                   ws.number_to_dp(self.intercept,
                                   DP))
        h += tr_qa("Logistic slope",
                   ws.number_to_dp(self.slope, DP))
        h += tr_qa("Logistic k (= slope)",
                   ws.number_to_dp(self.k, DP))
        h += tr_qa(u"Logistic theta (= –intercept/slope)",
                   ws.number_to_dp(self.theta, DP))
        h += tr_qa("Intensity for {}% detection".format(100*LOWER_MARKER),
                   ws.number_to_dp(self.logistic_x_from_p(LOWER_MARKER),
                                   DP))
        h += tr_qa("Intensity for 50% detection",
                   ws.number_to_dp(self.theta, DP))
        h += tr_qa("Intensity for {}% detection".format(100*UPPER_MARKER),
                   ws.number_to_dp(self.logistic_x_from_p(UPPER_MARKER),
                                   DP))
        h += u"""
            </table>
        """
        h += self.get_trial_html()
        return h