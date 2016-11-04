#pragma once
#include <QImage>
#include <QPen>
#include <QPoint>
#include <QSize>
#include <QFrame>

class QColor;
class QPaintEvent;
class QMouseEvent;

// See also http://stackoverflow.com/questions/28947235/qt-draw-on-canvas


class CanvasWidget : public QFrame
{
    // Widget for users to draw on a canvas (either blank, or with a starting
    // image).

    Q_OBJECT
public:
    CanvasWidget(QWidget* parent = nullptr);
    CanvasWidget(const QSize& size, QWidget* parent = nullptr);
    ~CanvasWidget();
    void setSize(const QSize& size);
    void setPen(const QPen& pen);
    void clear(const QColor& background);
    void setImage(const QImage& image, bool resize_widget = true);
    // ... if resize_widget is false, the image will be resized
    void drawTo(QPoint pt);
    virtual QSize sizeHint() const override;
    QImage image() const;
signals:
    void imageChanged();
protected:
    void commonConstructor(const QSize& size);
    virtual void paintEvent(QPaintEvent* event) override;
    virtual void mousePressEvent(QMouseEvent* event) override;
    virtual void mouseMoveEvent(QMouseEvent* event) override;
protected:
    QSize m_size;
    QImage m_image;
    QPen m_pen;
    QPoint m_point;
};