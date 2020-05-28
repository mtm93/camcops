/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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
#include "db/databaseobject.h"

class TaskScheduleItem : public DatabaseObject
{
    Q_OBJECT

public:
    // ------------------------------------------------------------------------
    // Creation
    // ------------------------------------------------------------------------

    TaskScheduleItem(CamcopsApp& app, DatabaseManager& db,
                     int load_pk = dbconst::NONEXISTENT_PK);
    TaskScheduleItem(int schedule_fk, CamcopsApp& app, DatabaseManager& db,
                     const QJsonObject json_obj);
    void addJsonFields(const QJsonObject json_obj);
    int id() const;
    QDate dueFrom() const;
    QDate dueBy() const;
    QString taskTableName() const;
    QString title() const;
    QString subtitle() const;
    bool active() const;

    static const QString TABLENAME;

    static const QString FN_TASK_TABLE_NAME;
    static const QString FN_DUE_FROM;
    static const QString FN_DUE_BY;
    static const QString FK_TASK_SCHEDULE;

    static const QString KEY_TABLE;
    static const QString KEY_DUE_FROM;
    static const QString KEY_DUE_BY;
};
