#include "./ui_dplm.h"
#include "./ui_endpointForm.h"
#include "./ui_writeForm.h"
#include "./ui_switchNetworkForm.h"
#include "dplm.h"

#include "dplm.h"
#include <QPushButton>
#include <string>
#include "httpRequest.hpp"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QMenu>
#include <thread>

Dplm::Dplm(
        Ui::Dplm* ui_,
        QWidget* parent )
    : QMainWindow(parent)
    , ui(ui_)
{
    ui->setupUi(this);
    connect(ui->device_tree, &QTreeWidget::itemDoubleClicked,
        this, &Dplm::listEndpoints);
    connect(this, &Dplm::listEndpointsS,
            this, &Dplm::listEndpointRequest);
    connect(ui->endpoint_tree, &QTreeWidget::itemDoubleClicked,
        this, &Dplm::endpointClicked);

    ui->endpoint_tree->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(ui->endpoint_tree, &QTreeWidget::customContextMenuRequested,
        this, &Dplm::endpointRightClicked);
    ui->device_tree->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(ui->device_tree, &QTreeWidget::customContextMenuRequested,
        this, &Dplm::deviceRightClicked);
    connect(ui->login_button, &QPushButton::released,
        this, &Dplm::loginClicked);

    connect(&this->web, &WebClientInterface::accepted,
        this, [=](std::string username,
                  std::string ip,
                  std::string port,
                  std::string token) {
            this->authToken = token;
            ui->hostName->setText(ip.c_str());  
            if (port != ""){
                ui->hostName->setText((ip+':'+port).c_str());
            }
            ui->login_state->setText(username.c_str());
            setupTree();
        });
    connect(ui->listDevicesButton, &QPushButton::released,
            this, &Dplm::listDevices);
    connect(this, &Dplm::gotListing,
            this, [=](QJsonDocument body){
        ui->device_tree->clear();
        std::cout << body.toJson().toStdString();
        for(auto grid_dict: body.array()){
            auto grid = grid_dict.toObject();
            QTreeWidgetItem* griditem = new QTreeWidgetItem();
            griditem->setText(0, grid.find("wifi_ssid").value().toString());
            for (auto device_dict: grid.find("devices")->toArray()){
                auto device = device_dict.toObject();
                QTreeWidgetItem* devitem = new QTreeWidgetItem();
                devitem->setText(1, device.find("clientID").value().toString());
                devitem->setText(2, device.find("local_address").value().toString());
                devitem->setText(3, device.find("last_update").value().toString());
                devitem->setText(4, device.find("wifi_ssid").value().toString());
                devitem->setData(0, Qt::UserRole + 1, QVariant(device_dict.toObject().find("id").value().toInt()));
                griditem->addChild(devitem);
            }
            ui->device_tree->addTopLevelItem(griditem);
        }
    });
    connect(this, &Dplm::gotEndpoints,
            this, [=](QJsonDocument body){
        ui->endpoint_tree->clear();
        for(auto dict: body.array()){
            auto endpoint = dict.toObject();
            QTreeWidgetItem* item = new QTreeWidgetItem();
            QString endpointName = endpoint.find("name").value().toString();
            item->setText(0, endpointName);
            ui->endpoint_tree->addTopLevelItem(item);
        }
    });
    connect(this, &Dplm::gotDeviceRead,
            this, [=](QTreeWidgetItem* item, QString resString){
        item->setText(1, resString);
        if (resString.size()==0)
            item->setText(1, "-");
    });
}

Dplm::~Dplm()
{
    delete ui;
}

std::string str(QString const& qstr){
    return qstr.toStdString();
}

void Dplm::deviceRightClicked(const QPoint& pos){
    QMenu menu(this);
    QTreeWidget *tree = ui->device_tree;
    QTreeWidgetItem *nd = tree->itemAt(pos);
    if (nd){
        this->currentSwitchWifiSsid = nd->text(0).toStdString();
        QAction *networkAct = new QAction("Switch network", this);
        connect(networkAct, &QAction::triggered,
                this, &Dplm::callSwitchNetworkProcedure);
        menu.addAction(networkAct);
    }
    menu.exec( tree->mapToGlobal(pos) );
}

void Dplm::callSwitchNetworkProcedure(){
    QDialog switchNetworkForm;
    Ui::SwitchNetworkForm uiform;
    uiform.setupUi(&switchNetworkForm);
    connect(uiform.buttonBox, &QDialogButtonBox::accepted,
            [=](){
        std::filesystem::path reqPath = "Dplm.postman_collection.json";
        http::RequestForm reqForm = http::readRequest(reqPath, "SwitchNetwork");
        http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
        reqForm.setHeader("Authorization", "Token " + this->authToken);
        reqForm.setHeader("Host", str(ui->hostName->text()));
        http::replace(reqForm.body, "$old_wifi_ssid", this->currentSwitchWifiSsid);
        http::replace(reqForm.body, "$wifi_ssid", uiform.wifiSsid->text().toStdString());
        http::replace(reqForm.body, "$wifi_pass", uiform.wifiPass->text().toStdString());
        const auto f = [=](){
            auto response = executeRequest(reqForm.urlRaw,
                                           reqForm.headers, reqForm.method);
            if (response.responseCode == 200){
                QJsonDocument body;
                body = QJsonDocument::fromJson(response.resultString.c_str());
                Q_EMIT this->gotListing(body);
            }
        };
        std::thread(f).detach();
    });
   switchNetworkForm.exec();
}

void Dplm::endpointRightClicked(const QPoint& pos){
    QMenu menu(this);
    QTreeWidget *tree = ui->endpoint_tree;
    QTreeWidgetItem *nd = tree->itemAt(pos);

    if (nd){
        this->endpointAction = nd->text(0).toStdString();
        this->inputFieldAction = nd->text(1).toStdString();
        QAction *plotAct = new QAction("Plot stream", this);
        plotAct->setStatusTip("Real time data plot");
        connect(plotAct, &QAction::triggered,
                this, &Dplm::callPlotProcedure);
        QAction *writeAct = new QAction("Write to device", this);
        connect(writeAct, &QAction::triggered,
                this, &Dplm::writeEndpointProcedure);
        menu.addAction(plotAct);
        menu.addAction(writeAct);
    } else { // new endpoint field
        QAction *addEndpointAct = new QAction("Add endpoint", this);
        connect(addEndpointAct, &QAction::triggered,
                this, &Dplm::addEndpointToDevice);
        menu.addAction(addEndpointAct);
    }
    menu.exec( tree->mapToGlobal(pos) );
}

void Dplm::addEndpointToDevice(){
    QDialog endpointForm;
    Ui::EndpointForm uiform;
    uiform.setupUi(&endpointForm);
    connect(uiform.buttonBox, &QDialogButtonBox::accepted,
            [=](){
        std::filesystem::path reqPath = "Dplm.postman_collection.json";
        http::RequestForm reqForm = http::readRequest(reqPath, "AddEndpoint");
        http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
        reqForm.setHeader("Authorization", "Token " + this->authToken);
        reqForm.setHeader("Host", str(ui->hostName->text()));
        http::replace(reqForm.body, "$name", uiform.name->text().toStdString());
        http::replace(reqForm.body, "$io_type", uiform.iotype->text().toStdString());
        http::replace(reqForm.body, "$data_type", uiform.datatype->text().toStdString());
        http::replace(reqForm.body, "$device", std::to_string(this->currentDevicePk));
        const auto f = [=](){
            executeRequest(reqForm.urlRaw,
                           reqForm.headers, reqForm.method, reqForm.body);
            Q_EMIT this->listEndpointsS(this->currentDevicePk);
        };
        std::thread(f).detach();
    });
    endpointForm.exec();

}

void Dplm::callPlotProcedure(){
    std::string argString;
    auto connection_vars = this->web.getAccessVariables();
    argString.append(connection_vars["username"] + ' ');
    argString.append(connection_vars["password"] + ' ');
    argString.append(this->currentClientID + ' ');
    argString.append(this->endpointAction + ' ');
    // TODO: get it from server!
    argString.append(this->broker_url + ' ');
    argString.append(this->broker_port);
    std::cout << argString << '\n';
    this->py.strFunc("plotSensor.py");
    const auto f = [=](){
        this->py.strFunc("plotSensor",
                   "execute",
                   argString);
    };
    std::thread(f).detach();
}

void Dplm::writeEndpointProcedure(){
    QDialog writeForm(this);
    Ui::WriteForm uiwrite;
    uiwrite.setupUi(&writeForm);
    writeForm.setWindowFlags(Qt::FramelessWindowHint | Qt::Popup);
    connect(uiwrite.buttonBox, &QDialogButtonBox::accepted,
            [=](){
        std::filesystem::path reqPath = "Dplm.postman_collection.json";
        http::RequestForm reqForm = http::readRequest(reqPath, "DeviceUpdate");
        http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
        reqForm.setHeader("Authorization", "Token " + this->authToken);
        reqForm.setHeader("Host", str(ui->hostName->text()));
        http::replace(reqForm.urlRaw,
                      "$device_pk", std::to_string(this->currentDevicePk));
        http::replace(reqForm.urlRaw,
                      "$endpoint", this->endpointAction);
        std::string str_payload;
        if (uiwrite.writeLine->text() != ""){
            try {
                int payload = std::stoi(uiwrite.writeLine->text().toStdString());
                str_payload += (unsigned char)payload;
            } catch (const std::exception & e) {
                str_payload = uiwrite.writeLine->text().toStdString();
            }
        } else { // no payload
            return;
        }
        reqForm.body = str_payload;
        const auto f = [=](){
            executeRequest(reqForm.urlRaw,
                           reqForm.headers, reqForm.method, reqForm.body);
        };
        std::thread(f).detach();
    });
    writeForm.exec();
}

void Dplm::loginClicked(){
    web.showClientWindow();
}

void Dplm::listDevices(){
    const auto f = [=](){
        std::filesystem::path reqPath = "Dplm.postman_collection.json";
        http::RequestForm reqForm = http::readRequest(reqPath, "ListGrids");
        http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
        reqForm.setHeader("Authorization", "Token " + this->authToken);
        reqForm.setHeader("Host", str(ui->hostName->text()));
        auto response = executeRequest(reqForm.urlRaw,
                                       reqForm.headers, reqForm.method);
        if (response.responseCode == 200){
            QJsonDocument body;
            body = QJsonDocument::fromJson(response.resultString.c_str());
            Q_EMIT this->gotListing(body);
        }
    };
    std::thread(f).detach();
}

void Dplm::setupTree()
{
    ui->device_tree->setSortingEnabled(false);
    ui->device_tree->clear();
    this->listDevices();
    ui->device_tree->setSortingEnabled(true);
}


void Dplm::listEndpointRequest(int pk)
{
    const auto f = [=](){
        std::filesystem::path reqPath = "Dplm.postman_collection.json";
        http::RequestForm reqForm = http::readRequest(reqPath, "ListEndpoints");
        http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
        http::replace(reqForm.urlRaw, "$device_pk", std::to_string(pk));
        reqForm.setHeader("Authorization", "Token " + this->authToken);
        reqForm.setHeader("Host", str(ui->hostName->text()));
        auto response = executeRequest(reqForm.urlRaw,
                                       reqForm.headers, reqForm.method);
        if (response.responseCode == 200){
            QJsonDocument body;
            body = QJsonDocument::fromJson(response.resultString.c_str());
            Q_EMIT this->gotEndpoints(body);
        }
    };
    std::thread(f).detach();
}

void Dplm::listEndpoints(QTreeWidgetItem* item, int column)
{
    Q_UNUSED(column);
    if (item->childCount() > 0)
        return;
    int id = item->data(0, Qt::UserRole + 1).toInt();
    this->currentDevicePk = id;
    this->currentClientID = item->text(1).toStdString();
    listEndpointRequest(id);
}


void Dplm::endpointClicked(QTreeWidgetItem* item, int column)
{
    Q_UNUSED(column);
    if (item->childCount() > 0)
        return;

    const auto f = [=](){
        std::filesystem::path reqPath = "Dplm.postman_collection.json";
        http::RequestForm reqForm = http::readRequest(reqPath, "GetDevice");
        http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
        http::replace(reqForm.urlRaw, "$id", std::to_string(currentDevicePk));
        reqForm.setHeader("Authorization", "Token " + this->authToken);
        reqForm.setHeader("Host", str(ui->hostName->text()));
        auto response = executeRequest(reqForm.urlRaw,
                                       reqForm.headers, reqForm.method);
        if (response.responseCode == 200){
            QJsonDocument body;
            body = QJsonDocument::fromJson(response.resultString.c_str());
            auto device = body.object();
            auto clientID = device.find("clientID").value().toString();
            http::RequestForm reqForm = http::readRequest(reqPath, "DeviceRead");
            http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
            reqForm.setHeader("Authorization", "Token " + this->authToken);
            reqForm.setHeader("Host", str(ui->hostName->text()));
            http::replace(reqForm.urlRaw,
                          "$device_pk", std::to_string(this->currentDevicePk));
            http::replace(reqForm.urlRaw,
                          "$endpoint", str(item->text(0)));
            executeRequest(reqForm.urlRaw,
                           reqForm.headers, reqForm.method,
                           reqForm.body);
            auto response = executeRequest(reqForm.urlRaw,
                                           reqForm.headers, reqForm.method,
                                           reqForm.body);
            if (response.responseCode == 200){
                Q_EMIT this->gotDeviceRead(item, QString(response.resultString.c_str()));
            }

        }
    };
    std::thread(f).detach();
}
