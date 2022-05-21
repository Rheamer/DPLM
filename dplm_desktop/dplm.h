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
#include <set>

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
    std::string authToken;
    WebClientInterface web;
    void setupTree();
    std::string endpointAction;
    std::string inputFieldAction;
    std::string currentClientID;
    std::string currentSwitchWifiSsid;
    int currentDevicePk = 0;
    PyUtils py;
    void callSwitchNetworkProcedure();
Q_SIGNALS:
    void closing();
    void listEndpointsS(int clientID);
    void gotListing(QJsonDocument body);
    void gotEndpoints(QJsonDocument body);
    void gotDeviceRead(QTreeWidgetItem* item, QString resultString);

private Q_SLOTS:
    void endpointClicked(QTreeWidgetItem *item, int column);
    void listEndpoints(QTreeWidgetItem *item, int column);
    void loginClicked();
    void endpointRightClicked(const QPoint &pos);
    void callPlotProcedure();
    void writeEndpointProcedure();
    void addEndpointToDevice();
    void listEndpointRequest(int clientID);
    void deviceRightClicked(const QPoint &pos);
};

#endif // USBCONNECTIONS_H
