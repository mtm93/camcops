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

#include "canvaswidget.h"
#include <QColor>
#include <QDebug>
#include <QMouseEvent>
#include <QPainter>
#include <QPaintEvent>
#include <QStyle>
#include <QStyleOption>
#include "widgets/margins.h"

const QPoint INVALID_POINT(-1, -1);


CanvasWidget::CanvasWidget(QWidget* parent) :
    QFrame(parent)
{
    commonConstructor(QSize(0, 0));
}


CanvasWidget::CanvasWidget(const QSize& size, QWidget* parent) :
    QFrame(parent)
{
    commonConstructor(size);
}


void CanvasWidget::commonConstructor(const QSize& size)
{
    m_point = INVALID_POINT;

    setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    setSize(size);

    // Default pen:
    m_pen.setColor(Qt::blue);
    m_pen.setWidth(2);
}


CanvasWidget::~CanvasWidget()
{
}


void CanvasWidget::setSize(const QSize& size)
{
    // qDebug() << Q_FUNC_INFO;
    m_size = size;
    update();
}


QSize CanvasWidget::sizeHint() const
{
    // Size of m_image (which is m_size), plus size of borders.
    // To do this, we have to derive from QFrame rather than QWidget, I think.

    // Several ways don't work.
    // - QWidget::sizeHint() returns QSize(-1, -1) despite stylesheet borders,
    //   even after ensurePolished().
    // - getContentsMargins() returns 0, 0, 0, 0 despite stylesheet borders, if
    //   you inherit from a QWidget. But if you inherit from a QFrame... yup,
    //   it works!

    Margins m = Margins::getContentsMargins(this);
    return m.addMarginsTo(m_size);
}


void CanvasWidget::setPen(const QPen& pen)
{
    m_pen = pen;
}


void CanvasWidget::clear(const QColor& background)
{
    // qDebug() << Q_FUNC_INFO;
    m_image.fill(background);
    update();
}


void CanvasWidget::setImage(const QImage &image, bool resize_widget)
{
    // qDebug() << Q_FUNC_INFO;
    if (resize_widget || !m_size.isValid()) {
        m_image = image;
        setSize(image.size());  // calls update()
    } else {
        // scale image onto m_canvas
        m_image = image.scaled(m_size);
        update();
    }
}


void CanvasWidget::paintEvent(QPaintEvent* event)
{
    Q_UNUSED(event);
    // If you derive from a QWidget, you can't find out how big the stylesheet
    // borders are, so you can't help overwriting them. So, derive from a
    // QFrame, and draw inside its contentsRect().
    // - https://forum.qt.io/topic/18325
    // - http://stackoverflow.com/questions/22415057

    // 1. The standard bits: background via stylesheet, etc.
    // - http://stackoverflow.com/questions/18344135

    QStyleOption o;
    o.initFrom(this);
    QPainter p(this);
    style()->drawPrimitive(QStyle::PE_Widget, &o, &p, this);

    // 2. Our bits
    QRect cr = contentsRect();
    p.drawImage(cr.left(), cr.top(), m_image);
}


void CanvasWidget::mousePressEvent(QMouseEvent* event)
{
    if (event->buttons() & Qt::LeftButton) {
        m_point = INVALID_POINT;
        drawTo(event->pos());
        update();
    }
}


void CanvasWidget::mouseMoveEvent(QMouseEvent* event)
{
    if (event->buttons() & Qt::LeftButton) {
        drawTo(event->pos());
        update();
    }
}


void CanvasWidget::drawTo(QPoint pt)
{
    if (m_image.isNull()) {
        qWarning() << Q_FUNC_INFO << "null image";
        return;
    }

    // Convert from widget coordinates (NB there's a frame) to image
    // coordinates:
    int left, top, right, bottom;
    getContentsMargins(&left, &top, &right, &bottom);
    pt.rx() -= left;
    pt.ry() -= top;

    // Draw
    QPainter p(&m_image);
    p.setPen(m_pen);
    QPoint from = m_point;
    if (from == INVALID_POINT) {
        from = pt;
    }
    p.drawLine(from, pt);
    m_point = pt;

    emit imageChanged();
}


QImage CanvasWidget::image() const
{
    return m_image;
}
