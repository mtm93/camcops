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

#include "qucanvas.h"
#include <QDebug>
#include <QHBoxLayout>
#include <QLabel>
#include <QTimer>
#include "common/uiconst.h"
#include "lib/convert.h"
#include "lib/timerfunc.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/canvaswidget.h"
#include "widgets/imagebutton.h"
#include "widgets/spacer.h"

const int WRITE_DELAY_MS = 200;


QuCanvas::QuCanvas(FieldRefPtr fieldref, const QSize& size, bool allow_shrink,
                   QImage::Format format, const QColor& background_colour) :
    m_fieldref(fieldref),
    m_size(size),
    m_allow_shrink(allow_shrink),
    m_format(format),
    m_background_colour(background_colour),
    m_using_template(false)
{
    commonConstructor();
}


QuCanvas::QuCanvas(FieldRefPtr fieldref, const QString& template_filename,
                   const QSize& size, bool allow_shrink) :
    m_fieldref(fieldref),
    m_size(size),
    m_allow_shrink(allow_shrink),
    m_background_colour(Qt::white),
    m_template_filename(template_filename),
    m_using_template(true)
{
    commonConstructor();
}


void QuCanvas::commonConstructor()
{
    Q_ASSERT(m_fieldref);
    m_adjust_for_dpi = true;
    m_border_width_px = 2;
    m_border_colour = uiconst::GREY_200;
    m_unused_space_colour = uiconst::TRANSPARENT;
    m_pen_colour = Qt::red;
    m_pen_width = 5;
    m_canvas = nullptr;
    m_missing_indicator = nullptr;
    m_no_missing_indicator = nullptr;
    m_field_write_pending = false;
    timerfunc::makeSingleShotTimer(m_timer);
    connect(m_timer.data(), &QTimer::timeout,
            this, &QuCanvas::completePendingFieldWrite);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuCanvas::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuCanvas::fieldValueChanged);
}


QuCanvas* QuCanvas::setAdjustForDpi(bool adjust_for_dpi)
{
    m_adjust_for_dpi = adjust_for_dpi;
    return this;
}


QuCanvas* QuCanvas::setBackgroundColour(const QColor& colour)
{
    m_background_colour = colour;
    return this;
}


QuCanvas* QuCanvas::setBorderWidth(int width)
{
    m_border_width_px = width;
    return this;
}


QuCanvas* QuCanvas::setBorderColour(const QColor& colour)
{
    m_border_colour = colour;
    return this;
}


QuCanvas* QuCanvas::setUnusedSpaceColour(const QColor& colour)
{
    m_unused_space_colour = colour;
    return this;
}


QuCanvas* QuCanvas::setPenColour(const QColor& colour)
{
    m_pen_colour = colour;
    return this;
}


QuCanvas* QuCanvas::setPenWidth(int width)
{
    m_pen_width = width;
    return this;
}


QuCanvas* QuCanvas::setAllowShrink(bool allow_shrink)
{
    m_allow_shrink = allow_shrink;
    return this;
}


QPointer<QWidget> QuCanvas::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    Qt::Alignment align = Qt::AlignLeft | Qt::AlignTop;

    m_canvas = new CanvasWidget();
    QPen pen;
    pen.setColor(m_pen_colour);
    pen.setWidth(m_pen_width);
    m_canvas->setPen(pen);
    m_canvas->setBorder(m_border_width_px, m_border_colour);
    m_canvas->setUnusedSpaceColour(m_unused_space_colour);
    m_canvas->setEnabled(!read_only);
    m_canvas->setAllowShrink(m_allow_shrink);
    if (!read_only) {
        connect(m_canvas.data(), &CanvasWidget::imageChanged,
                this, &QuCanvas::imageChanged);
    }

    QAbstractButton* button_reset = new ImageButton(uiconst::CBS_DELETE);
    button_reset->setEnabled(!read_only);
    if (!read_only) {
        connect(button_reset, &QAbstractButton::clicked,
                this, &QuCanvas::resetFieldToNull);
    }
    m_missing_indicator = uifunc::iconWidget(
                uifunc::iconFilename(uiconst::ICON_WARNING));
    m_no_missing_indicator = QPointer<Spacer>(new Spacer(uiconst::ICONSIZE));
    QVBoxLayout* button_layout = new QVBoxLayout();
    button_layout->setContentsMargins(uiconst::NO_MARGINS);
    button_layout->addWidget(button_reset, 0, align);
    button_layout->addWidget(m_missing_indicator, 0, align);
    button_layout->addWidget(m_no_missing_indicator, 0, align);
    QWidget* button_widget = new QWidget();
    button_widget->setLayout(button_layout);

    QHBoxLayout* top_layout = new QHBoxLayout();
    top_layout->setContentsMargins(uiconst::NO_MARGINS);
    top_layout->addWidget(button_widget, 0, align);
    top_layout->addWidget(m_canvas, 0, align);

    QWidget* widget = new QWidget();
    if (m_allow_shrink) {
        widget->setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Maximum);
    } else {
        widget->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    }
    widget->setLayout(top_layout);

    setFromField();
    return widget;
}


void QuCanvas::imageChanged()
{
    m_field_write_pending = true;
    m_timer->start(WRITE_DELAY_MS);  // goes to timerComplete
}


void QuCanvas::completePendingFieldWrite()
{
    if (!m_canvas || !m_field_write_pending) {
        return;
    }
    QImage img = m_canvas->image();
    bool changed = m_fieldref->setValue(img, this);
    m_field_write_pending = false;
    if (changed) {
        emit elementValueChanged();
    }
}


void QuCanvas::closing()
{
    completePendingFieldWrite();
}


void QuCanvas::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
}


void QuCanvas::fieldValueChanged(const FieldRef* fieldref,
                                 const QObject* originator)
{
    if (!m_canvas) {
        return;
    }

    // Mandatory: don't try to do it with a background; that doesn't work for
    // non-transparent templates, and it requires an immediate re-update when
    // the first strokes are drawn (but at all other times, we don't need to
    // redraw the widget when the user changes it).
    // So we'll do it with an indicator widget.

    bool missing_input = fieldref->missingInput();
    if (m_missing_indicator) {
        m_missing_indicator->setVisible(missing_input);
    }
    if (m_no_missing_indicator) {
        m_no_missing_indicator->setVisible(!missing_input);
    }
    // This prevents the overall widget's vertical size from changing (which
    // looks odd) on first draw, if the canvas is smaller vertically than the
    // two buttons/indicators.

    if (originator != this) {
        if (fieldref->isNull()) {
            resetWidget();
        } else {
            QImage img;
            bool success = img.loadFromData(fieldref->valueByteArray());
            if (success) {
                m_canvas->setImage(img);
            } else {
                qWarning() << Q_FUNC_INFO
                           << "- bad image data in field; resetting";
                resetWidget();
            }
        }
    }
}


FieldRefPtrList QuCanvas::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}


void QuCanvas::resetWidget()
{
    QImage img;
    bool make_duff_image = !m_using_template;
    bool use_source_image_size = true;
    QSize size = m_adjust_for_dpi
            ? convert::convertSizeByDpi(m_size, uiconst::DPI, uiconst::DEFAULT_DPI)
            : m_size;
    if (m_using_template) {
        if (img.load(m_template_filename)) {  // side effect!
            use_source_image_size = !size.isValid();
        } else {
            // Failed to load
            qWarning() << Q_FUNC_INFO << "- failed to load:"
                       << m_template_filename;
            make_duff_image = true;
        }
    }
    if (make_duff_image) {
        img = QImage(size, m_format);
        img.fill(m_background_colour);
    }
    bool resize = !use_source_image_size || m_adjust_for_dpi;
    m_canvas->setImage(img, !resize);  // if we're going to resize, don't do it twice/wrong
    if (resize) {
        m_canvas->setSize(size);
    }
}


void QuCanvas::resetFieldToNull()
{
    resetWidget();
    m_fieldref->setValue(QVariant(), this);
    emit elementValueChanged();
}
