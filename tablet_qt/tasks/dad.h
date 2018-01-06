/*
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
*/

#pragma once
#include <QString>
#include "tasklib/task.h"

class CamcopsApp;
class OpenableWidget;
class TaskFactory;

void initializeDad(TaskFactory& factory);


class Dad : public Task
{
    Q_OBJECT
public:
    Dad(CamcopsApp& app, DatabaseManager& db,
        int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
protected:
    QStringList getItemsActivity(const QString& activity) const;
    QStringList getItemsActivities(const QStringList& activities) const;
    QStringList getItemsPhase(const QString& phase) const;
    QString getScore(const QStringList& fieldnames) const;
public:
    static const QString DAD_TABLENAME;
};
