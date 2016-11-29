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

#pragma once
#include <QWidget>


class HeightForWidthLayoutContainer : public QWidget
{
    // A widget that knows that its layout implements a height-for-width
    // function and deals with it properly, adjusting the widget's height
    // to the layout (and its contents).
    // - SPECIFICALLY: IT WILL REDUCE ITS HEIGHT (TO FIT THE CONTENTS) AS THE
    //   LAYOUT SPREADS OUT CHILD WIDGETS TO THE RIGHT (in a way that a plain
    //   QWidget won't).
    // - Use this when you want to put a FlowLayout in (e.g. see QuMCQ).
    // - You might also use this when you want a widget containing a layout
    //   containing a LabelWordWrapWide object, or similar (e.g. see
    //   ClickableLabelWordWrapWide -- though that has to re-implement, not
    //   inherit, for Qt inheritance reasons).
    Q_OBJECT
public:
    HeightForWidthLayoutContainer(QWidget* parent = nullptr);
    virtual ~HeightForWidthLayoutContainer();
    virtual void resizeEvent(QResizeEvent* event) override;
};