// #define TEST_QT_BASIC
#define FULL_LOG_FORMAT

#ifdef TEST_QT_BASIC
#include <QApplication>  // for minimal_qt_app
#include <QPushButton>  // for minimal_qt_app
#endif
#include <QDebug>  // for qSetMessagePattern
#include "common/camcopsapp.h"

#ifdef FULL_LOG_FORMAT
const QString message_pattern =
    "camcops[%{threadid}]: %{time yyyy-MM-ddTHH:mm:ss.zzz}"
    ": %{type}: %{file}(%{line}): %{message}";
#else
const QString message_pattern = "camcops: %{type}: %{message}";
#endif


#ifdef TEST_QT_BASIC
int runMinimalQtAapp(int& argc, char *argv[])
{
    QApplication app(argc, argv);
    QPushButton button("Hello, world!");
    button.show();
    return app.exec();
}
#endif


int main(int argc, char *argv[])
{
    // NOTE: argc must be passed as a REFERENCE to int, or the app will
    // crash. See
    // https://bugreports.qt.io/browse/QTBUG-5637
    // http://doc.qt.io/qt-5/qapplication.html

#ifdef TEST_QT_BASIC
    // For when it all breaks!
    return runMinimalQtAapp(argc, argv);
#else
    // - The VERY FIRST THING we do is to create a QApplication, and that
    //   requires one bit of preamble.
    //   http://stackoverflow.com/questions/27963697
    // - Prevent native styling, which makes (for example) QListWidget colours
    //   not work from the stylsheet. This must be done before the app is
    //   created. See https://bugreports.qt.io/browse/QTBUG-45517

    QApplication::setStyle("fusion");

    qSetMessagePattern(message_pattern);
    // See also http://stackoverflow.com/questions/4954140/how-to-redirect-qdebug-qwarning-qcritical-etc-output
    CamcopsApp app(argc, argv);
    return app.run();
#endif
}