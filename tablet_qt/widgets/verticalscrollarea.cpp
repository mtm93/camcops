#include "verticalscrollarea.h"
#include <QDebug>
#include <QEvent>
#include <QScrollBar>


VerticalScrollArea::VerticalScrollArea(QWidget* parent) :
    QScrollArea(parent)
{
    setWidgetResizable(true);
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    // RNC addition:
    QSizePolicy sp(QSizePolicy::Expanding, QSizePolicy::Maximum);
    setSizePolicy(sp);
}


bool VerticalScrollArea::eventFilter(QObject* o, QEvent* e)
{
    // This works because QScrollArea::setWidget installs an eventFilter on the
    // widget
    if (o && o == widget() && e->type() == QEvent::Resize) {
        // RNC: HORIZONTAL: this plus the Expanding policy.
        setMinimumWidth(widget()->minimumSizeHint().width() +
                        verticalScrollBar()->width());
        /*
        // RNC:
        qDebug() << "minimumHeight():" << minimumHeight();
        qDebug() << "minimumSizeHint():" << minimumSizeHint();
        qDebug() << "size():" << size();
        qDebug() << "sizeHint():" << sizeHint();
        qDebug() << "widget()->size():" << widget()->size();
        qDebug() << "widget()->sizeHint():" << widget()->sizeHint();
        */
    }
    return QScrollArea::eventFilter(o, e);
}


// RNC addition:
// VERTICAL.
// Without this (and a vertical size policy of Maximum), it's very hard to
// get the scroll area to avoid one of the following:
// - expand too large vertically; distribute its contents vertically; thus
//   need an internal spacer at the end of its contents; thus have a duff
//   endpoint;
// - be too small vertically (e.g. if a spacer is put below it to prevent it
//   expanding too much) when there is vertical space available to use.
// So the answer it a Maximum vertical size policy, and a size hint that is
// exactly that of its contents.

QSize VerticalScrollArea::sizeHint() const
{
    return widget()->sizeHint();
}