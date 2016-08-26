#pragma once
#include <QMap>
#include <QPointer>
#include <QSharedPointer>
#include <QVariant>
#include "lib/fieldref.h"
#include "widgets/tickslider.h"  // or style sheets + tick marks don't mix
#include "namevalueoptions.h"
#include "quelement.h"

class QLabel;
class QTimer;


class QuSlider : public QuElement
{
    Q_OBJECT
public:
    QuSlider(FieldRefPtr fieldref, int minimum, int maximum, int step);
    QuSlider* setBigStep(int big_step);
    QuSlider* setTickInterval(bool tick_interval);  // 0 for none
    QuSlider* setTickPosition(QSlider::TickPosition position);
    QuSlider* setNullApparentValue(int null_apparent_value);
    QuSlider* setConvertForRealField(bool convert_for_real_field,
                                     double field_minimum = 0,
                                     double field_maximum = 1,
                                     int display_dp = 2);
    QuSlider* setHorizontal(bool horizontal);
    QuSlider* setShowValue(bool show_value);
    QuSlider* setTickLabels(const QMap<int, QString>& labels);
    QuSlider* setTickLabelPosition(QSlider::TickPosition position);
    QuSlider* setUseDefaultTickLabels(bool use_default);
    void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual FieldRefPtrList fieldrefs() const override;
    int sliderValueFromField(const QVariant& field_value) const;
    QVariant fieldValueFromSlider(int slider_value) const;
    virtual void closing() override;
protected slots:
    void sliderValueChanged(int slider_value);
    void completePendingFieldWrite();
    void fieldValueChanged(const FieldRef* fieldref,
                           const QObject* originator = nullptr);
protected:
    // Core
    FieldRefPtr m_fieldref;
    int m_minimum;
    int m_maximum;
    int m_step;
    int m_big_step;
    bool m_convert_for_real_field;
    double m_field_minimum;
    double m_field_maximum;
    int m_display_dp;
    int m_null_apparent_value;
    // Visuals
    bool m_horizontal;
    bool m_show_value;
    int m_tick_interval;
    QSlider::TickPosition m_tick_position;
    bool m_use_default_labels;
    QMap<int, QString> m_tick_labels;
    QSlider::TickPosition m_tick_label_position;
    // Internals
    QPointer<QLabel> m_value_label;
    QPointer<TickSlider> m_slider;
    bool m_field_write_pending;
    int m_field_write_slider_value;
    QSharedPointer<QTimer> m_timer;
};