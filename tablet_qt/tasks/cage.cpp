/*
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
*/

#include "cage.h"
#include "lib/mathfunc.h"
#include "lib/stringfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "tasklib/taskfactory.h"
using mathfunc::noneNull;
using mathfunc::scoreString;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;
using uifunc::yesNo;

const int FIRST_Q = 1;
const int N_QUESTIONS = 4;
const int MAX_SCORE = N_QUESTIONS;
const QString QPREFIX("q");

const QString CAGE_TABLENAME("cage");

const int CAGE_THRESHOLD = 2;


void initializeCage(TaskFactory& factory)
{
    static TaskRegistrar<Cage> registered(factory);
}


Cage::Cage(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, CAGE_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Cage::shortname() const
{
    return "CAGE";
}


QString Cage::longname() const
{
    return tr("CAGE Questionnaire");
}


QString Cage::menusubtitle() const
{
    return tr("4-item Y/N self-report scale.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Cage::isComplete() const
{
    return noneNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


QStringList Cage::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), MAX_SCORE)};
}


QStringList Cage::detail() const
{
    int total = totalScore();
    QStringList lines = fieldSummaries("q", "_s", " ",
                                       QPREFIX, FIRST_Q, N_QUESTIONS);
    lines.append("");
    lines += summary();
    lines.append("");
    lines.append(xstring("over_threshold") + " " +
                 yesNo(total >= CAGE_THRESHOLD));
    return lines;
}


OpenableWidget* Cage::editor(bool read_only)
{
    NameValueOptions options = CommonOptions::yesNoChar();
    QList<QuestionWithOneField> qfields;
    for (int n = FIRST_Q; n <= N_QUESTIONS; ++n) {
        QString question = xstring(strnum("q", n));
        QString fieldname = strnum(QPREFIX, n);
        qfields.append(QuestionWithOneField(question, fieldRef(fieldname)));
    }
    QuPagePtr page((new QuPage{
        new QuText(xstring("stem")),
        new QuMcqGrid(qfields, options),
    })->setTitle(xstring("title")));

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Cage::totalScore() const
{
    int total = 0;
    for (int i = FIRST_Q; i <= N_QUESTIONS; ++i) {
        total += score(value(strnum(QPREFIX, i)));
    }
    return total;
}


int Cage::score(const QVariant& value) const
{
    return value.toString() == CommonOptions::YES_CHAR ? 1 : 0;
    // ... returns 0 for null
}