#pragma once
#include "quelement.h"


class QuSpacer : public QuElement
{
public:
    QuSpacer();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
};