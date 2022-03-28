#ifndef USBCONNECTIONS_H
#define USBCONNECTIONS_H

#include <QMainWindow>
#include <QMap>
#include <QScopedPointer>
#include <QThread>
#include <QTreeWidget>
#include <unordered_set>

QT_BEGIN_NAMESPACE
namespace Ui {
class Dplm;
}
QT_END_NAMESPACE

class Dplm : public QMainWindow {
    Q_OBJECT

public:
    Dplm(Ui::Dplm* ui_,
         QWidget* parent = nullptr );
    ~Dplm();

private:
    Ui::Dplm *ui;
    void listDevices();
    int lastClickedDevice = 0;
    std::string authToken;

    void setupTree();
Q_SIGNALS:
    void closing();

private Q_SLOTS:
    void endpointClicked(QTreeWidgetItem *item, int column);
    void itemClicked(QTreeWidgetItem *item, int column);
};

#endif // USBCONNECTIONS_H
