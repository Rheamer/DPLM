#include "./ui_dplm.h"
#include "dplm.h"

#include "dplm.h"
#include <QPushButton>
#include <string>
#include "httpRequest.hpp"
#include "python_utilities.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QMenu>

Dplm::Dplm(
        Ui::Dplm* ui_,
        QWidget* parent )
    : QMainWindow(parent)
    , ui(ui_)
{
    ui->setupUi(this);
    connect(ui->device_tree, &QTreeWidget::itemDoubleClicked,
        this, &Dplm::itemClicked);
    connect(ui->endpoint_tree, &QTreeWidget::itemDoubleClicked,
        this, &Dplm::endpointClicked);

    this->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(ui->endpoint_tree, &QTreeWidget::customContextMenuRequested,
        this, &Dplm::endpointRightClicked);
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
    connect(this, &Dplm::gotListing,
            this, [=](QJsonDocument body){
        std::cout << body.toJson().toStdString();
        for(auto device_dict: body.array()){
            auto device = device_dict.toObject();
            QTreeWidgetItem* devitem = new QTreeWidgetItem();

            devitem->setText(0, device.find("clientID").value().toString());
            devitem->setText(1, device.find("local_address").value().toString());
            devitem->setText(2, device.find("last_update").value().toString());
            devitem->setText(3, device.find("wifi_ssid").value().toString());

            ui->device_tree->addTopLevelItem(devitem);
            devitem->setData(0, Qt::UserRole + 1, QVariant(device_dict.toObject().find("id").value().toInt()));
        }
    });
    connect(this, &Dplm::gotEndpoints,
            this, [=](QJsonDocument body){
        for(auto dict: body.array()){
            ui->endpoint_tree->clear();
            auto endpoint = dict.toObject();
            QTreeWidgetItem* item = new QTreeWidgetItem();
            item->setText(0, endpoint.find("name").value().toString());
            item->setData(0, Qt::UserRole + 1, QVariant(this->lastClickedDevice));
            ui->endpoint_tree->addTopLevelItem(item);
        }
    });
    connect(this, &Dplm::gotDeviceRead,
            this, [=](QTreeWidgetItem* item, std::string resString){
            item->setText(1, resString.c_str());
    });
}

Dplm::~Dplm()
{
    delete ui;
}

std::string str(QString const& qstr){
    return qstr.toStdString();
}

void Dplm::endpointRightClicked(const QPoint& pos){
    QTreeWidget *tree = ui->endpoint_tree;
    QTreeWidgetItem *nd = tree->itemAt(pos);

    QAction *plotAct = new QAction("Plot stream", this);
    plotAct->setStatusTip("Real time data plot");
    connect(plotAct, &QAction::triggered,
            this, &Dplm::callPlotProcedure);
    QMenu menu(this);
    menu.addAction(plotAct);
    menu.exec( tree->mapToGlobal(pos) );
}

void Dplm::callPlotProcedure(){
    PyUtils py;
    std::string argString;
    auto connection_vars = this->web.getAccessVariables();
    argString.append(connection_vars["username"] + ' ');
    argString.append(connection_vars["password"] + ' ');
    std::string clientID = ui->device_tree
            ->topLevelItem(this->lastClickedDevice)
            ->text(0).toStdString();
    argString.append(clientID + ' ');
    std::string topic = "action/read/stream/" + clientID;
    argString.append(topic + ' ');
    // TODO: get it from server!
    argString.append(this->broker_url + ' ');
    argString.append(this->broker_port);
    py.strFunc("plot_scripts/plotSensor.py",
               "execute",
               argString);
}

void Dplm::loginClicked(){
    web.showClientWindow();
}

void Dplm::listDevices(){
    const auto f = [=](){
        std::filesystem::path reqPath = "Dplm.postman_collection.json";
        http::RequestForm reqForm = http::readRequest(reqPath, "ListDevices");
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


void Dplm::itemClicked(QTreeWidgetItem* item, int column)
{
    Q_UNUSED(column);
    if (item->childCount() > 0)
        return;
    int id = item->data(0, Qt::UserRole + 1).toInt();
    this->lastClickedDevice = id;
    const auto f = [=](){
        std::filesystem::path reqPath = "Dplm.postman_collection.json";
        http::RequestForm reqForm = http::readRequest(reqPath, "ListEndpoints");
        http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
        http::replace(reqForm.urlRaw, "$client_id", std::to_string(id));
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


void Dplm::endpointClicked(QTreeWidgetItem* item, int column)
{
    Q_UNUSED(column);
    if (item->childCount() > 0)
        return;
    int device_id = item->data(0, Qt::UserRole + 1).toInt();
    const auto f = [=](){
        std::filesystem::path reqPath = "Dplm.postman_collection.json";
        http::RequestForm reqForm = http::readRequest(reqPath, "GetDevice");
        http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
        http::replace(reqForm.urlRaw, "$id", std::to_string(device_id));
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
            http::replace(reqForm.body, "$clientID", str(clientID));
            http::replace(reqForm.body, "$endpoint", str(item->text(0)));
            executeRequest(reqForm.urlRaw,
                           reqForm.headers, reqForm.method,
                           reqForm.body);
            auto response = executeRequest(reqForm.urlRaw,
                                           reqForm.headers, reqForm.method,
                                           reqForm.body);
            if (response.responseCode == 200){
                Q_EMIT this->gotDeviceRead(item, response.resultString);
            }

        }
    };
    std::thread(f).detach();
}
