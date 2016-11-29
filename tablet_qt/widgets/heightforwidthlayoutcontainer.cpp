/*
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

#include "heightforwidthlayoutcontainer.h"
// #include <QDebug>
#include <QLayout>
#include "lib/uifunc.h"


HeightForWidthLayoutContainer::HeightForWidthLayoutContainer(QWidget* parent) :
    QWidget(parent)
{
    // As for LabelWordWrapWide:
    setSizePolicy(UiFunc::expandingFixedHFWPolicy());
}


HeightForWidthLayoutContainer::~HeightForWidthLayoutContainer()
{
    // qDebug() << Q_FUNC_INFO;
}


void HeightForWidthLayoutContainer::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    UiFunc::resizeEventForHFWParentWidget(this);
}