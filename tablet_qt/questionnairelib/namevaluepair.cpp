#include "namevaluepair.h"

NameValuePair::NameValuePair(const QString& name, const QVariant& value) :
    m_name(name),
    m_value(value)
{
    Q_ASSERT(!m_value.isNull());
}


const QString& NameValuePair::name() const
{
    return m_name;
}


const QVariant& NameValuePair::value() const
{
    return m_value;
}
