/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#include "setmenulynall1iam.h"
#include "common/textconst.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/audit.h"
#include "tasks/cisr.h"
#include "tasks/ctqsf.h"
#include "tasks/lynall1iammedical.h"
#include "tasks/lynall2iamlife.h"
#include "tasks/rand36.h"


SetMenuLynall1IAM::SetMenuLynall1IAM(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETS_RESEARCH))
{
}


QString SetMenuLynall1IAM::title() const
{
    return tr("Lynall M-E — 1 — IAM study");
}


QString SetMenuLynall1IAM::subtitle() const
{
    return tr("Lynall M-E, University of Cambridge, UK — "
              "Inflammation in Mind (IAM) study");
}


void SetMenuLynall1IAM::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MAKE_TASK_MENU_ITEM(Audit::AUDIT_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Cisr::CISR_TABLENAME, m_app),
        // *** // MAKE_TASK_MENU_ITEM(Ctqsf::CTQSF_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Lynall1IamMedical::LYNALL_1_IAM_MEDICAL_TABLENAME, m_app),
        // *** // MAKE_TASK_MENU_ITEM(Lynall2IamLife::LYNALL_2_IAM_LIFE_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Rand36::RAND36_TABLENAME, m_app),
    };
}