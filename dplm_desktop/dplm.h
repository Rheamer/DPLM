#ifndef USBCONNECTIONS_H
#define USBCONNECTIONS_H

#include <QMainWindow>
#include <QMap>
#include <QScopedPointer>
#include <QThread>
#include <QTreeWidget>
#include <unordered_set>
#include "web_client.hpp"
#include "python_utilities.h"
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
    // TODO: get it from server!
    std::string broker_url = "dff8we.stackhero-network.com";
    std::string broker_port = "1883";
    void listDevices();
    int lastClickedClientID = 0;
    int lastClickedClientIndex = 0;
    std::string authToken;
    WebClientInterface web;
    void setupTree();
    std::string clientIDForStream;
    std::string endpointForStream;
    PyUtils py;
Q_SIGNALS:
    void closing();
    void gotListing(QJsonDocument body);
    void gotEndpoints(QJsonDocument body);
    void gotDeviceRead(QTreeWidgetItem* item, std::string resultString);

private Q_SLOTS:
    void endpointClicked(QTreeWidgetItem *item, int column);
    void itemClicked(QTreeWidgetItem *item, int column);
    void loginClicked();
    void endpointRightClicked(const QPoint &pos);
    void callPlotProcedure();
};

#endif // USBCONNECTIONS_H
