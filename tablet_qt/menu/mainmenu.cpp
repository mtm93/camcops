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

#include "mainmenu.h"
#include <QDebug>
#include <QSharedPointer>
#include "common/uiconst.h"
#include "core/networkmanager.h"
#include "dbobjects/taskschedule.h"
#include "dbobjects/taskscheduleitem.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"
#include "menulib/menuproxy.h"

#include "menu/addictionmenu.h"
#include "menu/affectivemenu.h"
#include "menu/alltasksmenu.h"
#include "menu/anonymousmenu.h"
#include "menu/catatoniaepsemenu.h"
#include "menu/clinicalmenu.h"
#include "menu/clinicalsetsmenu.h"
#include "menu/cognitivemenu.h"
#include "menu/executivemenu.h"
#include "menu/globalmenu.h"
#include "menu/helpmenu.h"
#include "menu/patientsummarymenu.h"
#include "menu/personalitymenu.h"
#include "menu/physicalillnessmenu.h"
#include "menu/psychosismenu.h"
#include "menu/researchmenu.h"
#include "menu/researchsetsmenu.h"
#include "menu/serviceevaluationmenu.h"
#include "menu/settingsmenu.h"


MainMenu::MainMenu(CamcopsApp& app)
    : MenuWindow(
          app,
          uifunc::iconFilename(uiconst::ICON_CAMCOPS),
          true)
{
    connect(&m_app, &CamcopsApp::modeChanged,
            this, &MainMenu::modeChanged,
            Qt::UniqueConnection);
}


QString MainMenu::title() const
{
    return tr("CamCOPS: Cambridge Cognitive and Psychiatric Assessment Kit");
}


void MainMenu::makeItems()
{
    if (m_app.isClinicianMode()) {
        makeClinicianItems();
    } else {
        makeSingleUserItems();
    }

    connect(&m_app, &CamcopsApp::fontSizeChanged,
            this, &MainMenu::reloadStyleSheet);
}


void MainMenu::makeClinicianItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MAKE_MENU_MENU_ITEM(PatientSummaryMenu, m_app),
        MenuItem(
            tr("Upload data to server"),
            std::bind(&MainMenu::upload, this),
            uifunc::iconFilename(uiconst::ICON_UPLOAD)
        ).setNotIfLocked(),
        MAKE_MENU_MENU_ITEM(HelpMenu, m_app),
        MAKE_MENU_MENU_ITEM(SettingsMenu, m_app),

        MenuItem(tr("Tasks by type")).setLabelOnly(),
        MAKE_MENU_MENU_ITEM(ClinicalMenu, m_app),
        MAKE_MENU_MENU_ITEM(GlobalMenu, m_app),
        MAKE_MENU_MENU_ITEM(CognitiveMenu, m_app),
        MAKE_MENU_MENU_ITEM(AffectiveMenu, m_app),
        MAKE_MENU_MENU_ITEM(AddictionMenu, m_app),
        MAKE_MENU_MENU_ITEM(PsychosisMenu, m_app),
        MAKE_MENU_MENU_ITEM(CatatoniaEpseMenu, m_app),
        MAKE_MENU_MENU_ITEM(PersonalityMenu, m_app),
        MAKE_MENU_MENU_ITEM(ExecutiveMenu, m_app),
        MAKE_MENU_MENU_ITEM(PhysicalIllnessMenu, m_app),
        MAKE_MENU_MENU_ITEM(ServiceEvaluationMenu, m_app),
        MAKE_MENU_MENU_ITEM(ResearchMenu, m_app),
        MAKE_MENU_MENU_ITEM(AnonymousMenu, m_app),

        MenuItem(tr("Task collections")).setLabelOnly(),
        MAKE_MENU_MENU_ITEM(ClinicalSetsMenu, m_app),
        MAKE_MENU_MENU_ITEM(ResearchSetsMenu, m_app),
        MAKE_MENU_MENU_ITEM(AllTasksMenu, m_app),
    };
}


void MainMenu::makeSingleUserItems()
{
    m_items = {};

    TaskSchedulePtrList schedules = m_app.getTaskSchedules();

    for (const TaskSchedulePtr& schedule : schedules) {
        QVector<MenuItem> started_items = {};
        QVector<MenuItem> due_items = {};
        QVector<MenuItem> completed_items = {};
        QVector<MenuItem> missed_items = {};
        QVector<MenuItem> future_items = {};

        for (const TaskScheduleItemPtr& schedule_item : schedule->items()) {
            auto state = schedule_item->state();

            switch (state) {

            case TaskScheduleItem::State::Started:
                started_items.append(TaskScheduleItemMenuItem(schedule_item));
                break;

            case TaskScheduleItem::State::Completed:
                completed_items.append(TaskScheduleItemMenuItem(schedule_item));
                break;

            case TaskScheduleItem::State::Missed:
                missed_items.append(TaskScheduleItemMenuItem(schedule_item));
                break;

            case TaskScheduleItem::State::Due:
                due_items.append(TaskScheduleItemMenuItem(schedule_item));
                break;

            case TaskScheduleItem::State::Future:
                future_items.append(TaskScheduleItemMenuItem(schedule_item));
                break;

            default:
                break;
            }
        }

        if (started_items.size() > 0) {
            m_items.append(
                MenuItem(
                    tr("Started tasks for %1").arg(schedule->name())
                ).setLabelOnly()
            );

            m_items.append(started_items);
        }

        if (due_items.size() > 0) {
            m_items.append(
                MenuItem(
                    tr("Due tasks for %1").arg(schedule->name())
                ).setLabelOnly()
            );

            m_items.append(due_items);
        }

        if (future_items.size() > 0) {
            m_items.append(
                MenuItem(
                    tr("Future tasks for %1").arg(schedule->name())
                ).setLabelOnly()
            );

            m_items.append(future_items);
        }

        if (completed_items.size() > 0) {
            m_items.append(
                MenuItem(
                    tr("Completed tasks for %1").arg(schedule->name())
                ).setLabelOnly()
            );

            m_items.append(completed_items);
        }

        if (missed_items.size() > 0) {
            m_items.append(
                MenuItem(
                    tr("Missed tasks for %1").arg(schedule->name())
                ).setLabelOnly()
            );

            m_items.append(missed_items);
        }

    }

    if (m_items.size() == 0) {
        m_items.append(
            MenuItem(tr("You do not have any scheduled tasks")).setLabelOnly()
        );
    }

    QVector<MenuItem> registration_items = {
        MenuItem(tr("Patient registration")).setLabelOnly(),
    };

    registration_items.append(
        MenuItem(
            tr("Register patient"),
            std::bind(&MainMenu::registerPatient, this)
            ).setNotIfLocked()
    );

    if (!m_app.needToRegisterSinglePatient()) {
        registration_items.append(
            MenuItem(
                tr("Update schedules"),
                std::bind(&MainMenu::updateTaskSchedules, this)
            ).setNotIfLocked()
        );
    }

    m_items.append(registration_items);

    QVector<MenuItem> settings_items = {
        MenuItem(tr("Settings")).setLabelOnly(),
        MenuItem(
            tr("Change operating mode"),
            std::bind(&MainMenu::changeMode, this)
        ).setNotIfLocked(),
    };

    m_items.append(settings_items);
}


void MainMenu::updateTaskSchedules()
{
    m_app.updateTaskSchedules();
}


void MainMenu::upload()
{
    m_app.upload();
}


void MainMenu::changeMode()
{
    m_app.setModeFromUser();
}


void MainMenu::modeChanged(const int mode)
{
    Q_UNUSED(mode);

#ifdef DEBUG_SLOTS
    qDebug() << Q_FUNC_INFO << "[this:" << this << "]";
#endif
    rebuild();
}


void MainMenu::registerPatient()
{
    m_app.registerPatientWithServer();
}
