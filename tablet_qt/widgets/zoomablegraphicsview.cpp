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

#define DEBUG_COORDS

#include "zoomablegraphicsview.h"
#include <QDebug>
#include <QWheelEvent>


// ============================================================================
// Constructor
// ============================================================================

ZoomableGraphicsView::ZoomableGraphicsView(
        QGraphicsScene* scene,
        const bool can_scale_smaller_than_viewport,
        const qreal min_scale,
        const qreal max_scale,
        const qreal scale_step_factor) :
    QGraphicsView(scene),
    m_can_scale_smaller_than_viewport(can_scale_smaller_than_viewport),
    m_min_scale(min_scale),
    m_max_scale(max_scale),
    m_scale_step_factor(scale_step_factor),
    m_scale(1.0),
    m_smallest_fit_scale(1.0)  // until fitView() is called
{
    // See https://code.qt.io/cgit/qt/qtbase.git/tree/examples/widgets/touch/pinchzoom/graphicsview.cpp?h=5.13
    viewport()->setAttribute(Qt::WA_AcceptTouchEvents);
    setDragMode(ScrollHandDrag);

    const Qt::ScrollBarPolicy sbp = Qt::ScrollBarAlwaysOn;
    // const Qt::ScrollBarPolicy sbp = Qt::ScrollBarAsNeeded;  // too tricky; see resizeEvent()
    setHorizontalScrollBarPolicy(sbp);
    setVerticalScrollBarPolicy(sbp);

    setFrameShape(QFrame::NoFrame);

    // Make sure the contents are at the top left of our view, when all of the
    // contents are visible.
    setAlignment(Qt::AlignLeft | Qt::AlignTop);
}


// ============================================================================
// Ways that the zoom can change
// ============================================================================

void ZoomableGraphicsView::wheelEvent(QWheelEvent* event)
{
    // https://github.com/glumpy/glumpy/issues/99
    const int steps = event->angleDelta().y() / 120;
    if (steps == 0) {
        return;  // nothing to do
    }
    if (steps > 0) {
        // zoom in (magnify); steps is positive
        m_scale *= m_scale_step_factor * steps;
    } else {
        // zoom out (shrink); steps is negative
        m_scale /= m_scale_step_factor * (-steps);
    }
#ifdef DEBUG_COORDS
    qDebug() << Q_FUNC_INFO << "steps" << steps << "m_scale" << m_scale;
#endif
    rescale();
}


bool ZoomableGraphicsView::viewportEvent(QEvent* event)
{
    // See https://code.qt.io/cgit/qt/qtbase.git/tree/examples/widgets/touch/pinchzoom/graphicsview.cpp?h=5.13
    switch (event->type()) {
    case QEvent::TouchBegin:
    case QEvent::TouchUpdate:
    case QEvent::TouchEnd:
        {
            QTouchEvent* touch_event = static_cast<QTouchEvent*>(event);
            QList<QTouchEvent::TouchPoint> touch_points = touch_event->touchPoints();
            if (touch_points.count() == 2) {
                // determine scale factor
                const QTouchEvent::TouchPoint& touchpoint0 = touch_points.first();
                const QTouchEvent::TouchPoint& touchpoint1 = touch_points.last();
                const qreal current_scale_factor =
                        QLineF(touchpoint0.pos(), touchpoint1.pos()).length()
                        / QLineF(touchpoint0.startPos(), touchpoint1.startPos()).length();
                // NB simplified from the original here; *** TEST TWO-FINGER ZOOM
                m_scale *= current_scale_factor;
                rescale();
            }
            return true;
        }
    default:
        break;
    }
    return QGraphicsView::viewportEvent(event);
}


// ============================================================================
// Other events
// ============================================================================

void ZoomableGraphicsView::resizeEvent(QResizeEvent* event)
{
    /*
    http://doc.qt.io/qt-5.8/qgraphicsview.html
    "Note though, that calling fitInView() from inside resizeEvent() can lead
    to unwanted resize recursion, if the new transformation toggles the
    automatic state of the scrollbars. You can toggle the scrollbar policies to
    always on or always off to prevent this (see horizontalScrollBarPolicy()
    and verticalScrollBarPolicy()).
    */

    Q_UNUSED(event);
    fitView();
}


void ZoomableGraphicsView::showEvent(QShowEvent* event)
{
    Q_UNUSED(event);
    fitView();
}


// ============================================================================
// Scaling
// ============================================================================

void ZoomableGraphicsView::rescale()
{
#ifdef DEBUG_COORDS
    qDebug().nospace() << Q_FUNC_INFO << ": initial m_scale " << m_scale;
#endif
    m_scale = qBound(m_min_scale, m_scale, m_max_scale);
    if (!m_can_scale_smaller_than_viewport) {
        m_scale = qMax(m_scale, m_smallest_fit_scale);
    }
#ifdef DEBUG_COORDS
    qDebug().nospace() << Q_FUNC_INFO << ": sceneRect() " << sceneRect()
                       << ", final m_scale " << m_scale;
#endif
    QTransform matrix;  // identity matrix
    matrix.scale(m_scale, m_scale);
    setTransform(matrix);
    update();
}


void ZoomableGraphicsView::fitView()
{
    const QRectF scene_rect = sceneRect();
#ifdef DEBUG_COORDS
    qDebug().nospace() << Q_FUNC_INFO << ": sceneRect() " << scene_rect;
#endif
    fitInView(scene_rect, Qt::KeepAspectRatio);
    // ... makes sceneRect() fit, and in the process sets the transform

    // A bit of ?hardcoded margin appears, e.g. 1 pixel around the edge.
    // - https://bugreports.qt.io/browse/QTBUG-42331

    // Now read the transform back so we know our scale
    const QTransform t = transform();
    qreal horiz_scale = t.m11();
#ifdef DEBUG_COORDS
    // Since we only call fitView() with the Qt::KeepAspectRatio parameter,
    // horiz_scale should also be the vertical scale factor, m22().
    // We can check that:
    const qreal vert_scale = t.m22();
    if (!qFuzzyCompare(horiz_scale, vert_scale)) {
        qWarning() << "Horizontal/vertical scale mismatch: h" << horiz_scale
                   << "v" << vert_scale;
    }
#endif
    if (horiz_scale > 1.0) {
        // We're not trying to zoom in unless asked to do so.
        // (Though we may have had to zoom out -- shrink -- for small screens.)
#ifdef DEBUG_COORDS
        qDebug().nospace()
                << Q_FUNC_INFO
                << ": Not scaling to " << horiz_scale << "; using 1.0 instead";
#endif
        horiz_scale = 1.0;
        setTransform(QTransform());  // identity matrix
    }
    m_scale = horiz_scale;
    m_smallest_fit_scale = m_scale;
#ifdef DEBUG_COORDS
    qDebug().nospace()
            << Q_FUNC_INFO
             << ": Setting m_scale and m_smallest_fit_scale to " << m_scale;
#endif
}