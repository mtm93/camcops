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


#include "geometry.h"
#include <QtMath>
#include "maths/mathfunc.h"
using mathfunc::mod;


namespace geometry
{


const qreal DEG_0 = 0.0;
const qreal DEG_90 = 90.0;
const qreal DEG_270 = 270.0;
const qreal DEG_180 = 180.0;
const qreal DEG_360 = 360.0;


int sixteenthsOfADegree(qreal degrees)
{
    // http://doc.qt.io/qt-5/qpainter.html#drawPie
    return qRound(degrees * 16.0);
}


qreal normalizeHeading(qreal heading_deg)
{
    return mod(heading_deg, DEG_360);
}


bool headingNearlyEq(qreal heading_deg, qreal value_deg)
{
    return qFuzzyIsNull(normalizeHeading(heading_deg - value_deg));
}


bool headingInRange(qreal first_bound_deg,
                    qreal heading_deg,
                    qreal second_bound_deg,
                    bool inclusive)
{
    // The values in degrees are taken as a COMPASS HEADING, i.e. increasing
    // is clockwise. The valid sector is defined CLOCKWISE from the first bound
    // to the second.
    first_bound_deg = normalizeHeading(first_bound_deg);
    heading_deg = normalizeHeading(heading_deg);
    second_bound_deg = normalizeHeading(second_bound_deg);
    // First, we deal with "on the boundary" conditions:
    if (heading_deg == first_bound_deg || heading_deg == second_bound_deg) {
        return inclusive;
    }
    bool range_increases = first_bound_deg < second_bound_deg;
    qreal lower_bound;
    qreal upper_bound;
    if (range_increases) {
        lower_bound = first_bound_deg;
        upper_bound = second_bound_deg;
    } else {
        lower_bound = second_bound_deg;
        upper_bound = first_bound_deg;
    }
    bool within = lower_bound < heading_deg && heading_deg < upper_bound;
    // Second bound is clockwise ("right") from first.
    // If the second bound is numerically greater than the first, then
    // we have a simple range that doesn't cross "North" (0 = 360),
    // and the heading is in range if it's within the two. For example,
    // if the range is (50, 70), then the heading is in range if
    // 50 < x < 70. However, if the range decreases, we're crossing North,
    // e.g. (350, 10); in that case, the heading is in range if and only if
    // it is NOT true that 10 < x < 350.
    return within == range_increases;
}


qreal convertHeadingFromTrueNorth(qreal true_north_heading_deg,
                                  qreal pseudo_north_deg,
                                  bool normalize)
{
    // Example: pseudo_north_deg is 30;
    // then 0 in true North is -30 in pseudo-North.
    qreal h = true_north_heading_deg - pseudo_north_deg;
    return normalize ? normalizeHeading(h) : h;
}


qreal convertHeadingToTrueNorth(qreal pseudo_north_heading_deg,
                                qreal pseudo_north_deg,
                                bool normalize)
{
    // Inverts convertHeadingFromTrueNorth().
    qreal h = pseudo_north_heading_deg + pseudo_north_deg;
    return normalize ? normalizeHeading(h) : h;
}


QPointF polarToCartesian(qreal r, qreal theta_deg)
{
    // theta == 0 implies along the x axis in a positive direction (right).
    qreal theta_rad = qDegreesToRadians(theta_deg);
    return QPointF(r * qCos(theta_rad), r * qSin(theta_rad));
}


qreal distanceBetween(const QPointF& from, const QPointF& to)
{
    qreal dx = to.x() - from.x();
    qreal dy = to.y() - from.y();
    // Pythagoras:
    return qSqrt(qPow(dx, 2) + qPow(dy, 2));
}


qreal polarThetaToHeading(qreal theta_deg, qreal north_deg)
{
    // Polar coordinates have theta 0 == East, and theta positive is
    // clockwise (in Qt coordinates with y down).
    // Compass headings have 0 == North, unless adjusted by
    // north_deg (e.g. specifying north_deg = 90 makes the heading 0 when
    // actually East), and positive clockwise.
    // - The first step converts to "clockwise, up is 0":
    qreal true_north_heading = theta_deg + DEG_90;
    return convertHeadingFromTrueNorth(true_north_heading, north_deg);
}


qreal headingToPolarTheta(qreal heading_deg, qreal north_deg, bool normalize)
{
    // Polar coordinates have theta 0 == East, and theta positive is
    // anticlockwise. Compass headings have 0 == North, unless adjusted by
    // north_deg (e.g. specifying north_deg = 90 makes the heading 0 when
    // actually East), and positive clockwise.
    qreal true_north_heading = convertHeadingToTrueNorth(
                heading_deg, north_deg, normalize);
    qreal theta = true_north_heading - DEG_90;
    return normalize ? normalizeHeading(theta) : theta;
}


qreal polarTheta(const QPointF& from, const QPointF& to)
{
    qreal dx = to.x() - from.x();
    qreal dy = to.y() - from.y();
    if (dx == 0 && dy == 0) {
        // Nonsensical; no movement.
        return 0.0;
    }
    // The arctan function will give us 0 = East, the geometric form.
    return qRadiansToDegrees(qAtan2(dy, dx));
}


qreal polarTheta(const QPointF& to)
{
    return polarTheta(QPointF(0, 0), to);
}


qreal headingDegrees(const QPointF& from, const QPointF& to, qreal north_deg)
{
    // Returns a COMPASS HEADING (0 is North = up).
    return polarThetaToHeading(polarTheta(from, to), north_deg);
}


bool lineSegmentsIntersect(const QPointF& first_from, const QPointF& first_to,
                           const QPointF& second_from, const QPointF& second_to)
{
    LineSegment s1(first_from, first_to);
    LineSegment s2(second_from, second_to);
    return s1.intersects(s2);
}


bool pointOnLineSegment(const QPointF& point,
                        const QPointF& line_start, const QPointF& line_end)
{
    LineSegment ls(line_start, line_end);
    return ls.pointOn(point);
}


LineSegment lineFromPointInHeadingWithRadius(const QPointF& point,
                                             qreal heading_deg,
                                             qreal north_deg,
                                             qreal radius)
{
    qreal theta = headingToPolarTheta(heading_deg, north_deg);
    QPointF distant_point = point + polarToCartesian(radius, theta);
    return LineSegment(point, distant_point);
}


bool lineCrossesHeadingWithinRadius(const QPointF& from, const QPointF& to,
                                    const QPointF& point, qreal heading_deg,
                                    qreal north_deg, qreal radius)
{
    // (1) Draw a line from "from" to "to".
    // (2) Draw a line from "point" in direction "heading", where increasing
    //     values of "heading" are clockwise, and a heading of 0 points in
    //     the North direction, where that is defined by north_deg degrees
    //     clockwise of "screen up".
    if (from == to) {
        return false;
    }
    LineSegment ls_trajectory = lineFromPointInHeadingWithRadius(
                point, heading_deg, radius, north_deg);
    LineSegment from_to = LineSegment(from, to);
    return from_to.intersects(ls_trajectory);
}


bool linePassesBelowPoint(const QPointF& from, const QPointF& to,
                          const QPointF& point)
{
    return lineCrossesHeadingWithinRadius(from, to, point, DEG_180, 0,
                                          QWIDGETSIZE_MAX);
}


}  // namespace geometry