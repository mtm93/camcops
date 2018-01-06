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
#include <QObject>

class QEvent;


class DebugEventWatcher : public QObject
{
    // Object to watch, and debug-log, all mouse/touch events on an object.
    Q_OBJECT
public:
    enum EventCategory {  // http://doc.qt.io/qt-5.9/qflags.html#details
        All = (1 << 0),
        MouseTouch = (1 << 1),
    };
    Q_DECLARE_FLAGS(EventCategories, EventCategory)
public:
    explicit DebugEventWatcher(QObject* parent, EventCategories categories);
    virtual bool eventFilter(QObject* obj, QEvent* event) override;
private:
    void report(QObject* obj, QEvent* event) const;
private:
    EventCategories m_categories;
};

Q_DECLARE_OPERATORS_FOR_FLAGS(DebugEventWatcher::EventCategories)
