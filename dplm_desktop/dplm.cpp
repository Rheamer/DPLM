#include "./ui_dplm.h"

#include "dplm.h"
#include <QPushButton>
#include <string>
#include "httpRequest.hpp"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>

Dplm::Dplm(
        Ui::Dplm* ui_,
        QWidget* parent )
    : QMainWindow(parent)
    , ui(ui_)
{
    ui->setupUi(this);
    setupTree();
    connect(ui->device_tree, &QTreeWidget::itemDoubleClicked,
        this, &Dplm::itemClicked);
    connect(ui->endpoint_tree, &QTreeWidget::itemDoubleClicked,
        this, &Dplm::endpointClicked);
}

Dplm::~Dplm()
{
    delete ui;
}

std::string str(QString const& qstr){
    return qstr.toStdString();
}

void Dplm::listDevices(){
    std::filesystem::path reqPath = "Dplm.postman_collection.json";
    http::RequestForm reqForm = http::readRequest(reqPath, "DeviceList");
    http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
    reqForm.setHeader("Authorization", this->authToken);
    reqForm.setHeader("Host", str(ui->hostName->text()));
    auto response = executeRequest(reqForm.urlRaw,
                                   reqForm.headers, reqForm.method);
    if (response.responseCode == 200){
        QJsonDocument body;
        body = QJsonDocument::fromJson(response.resultString.c_str());
        int device_index = 0;
        for(auto device_dict: body.array()){
            auto device = device_dict.toObject();
            int field_index = 0;
            QTreeWidgetItem* devitem = new QTreeWidgetItem(ui->device_tree->topLevelItem(device_index));
            for (int i =1; i<device_dict.toArray().size(); i++){
                devitem->setText(field_index, device_dict.toArray()[i].toString());
            }
            devitem->setData(0, Qt::UserRole + 1, QVariant(device.find("id").value().toInt()));
            device_index++;
        }
    }

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
    std::filesystem::path reqPath = "Dplm.postman_collection.json";
    http::RequestForm reqForm = http::readRequest(reqPath, "ListEndpoints");
    http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
    reqForm.setHeader("Authorization", this->authToken);
    reqForm.setHeader("Host", str(ui->hostName->text()));
    auto response = executeRequest(reqForm.urlRaw,
                                   reqForm.headers, reqForm.method);
    if (response.responseCode == 200){
        QJsonDocument body;
        body = QJsonDocument::fromJson(response.resultString.c_str());
        int index = 0;
        for(auto dict: body.array()){
            auto endpoint = dict.toObject();
            int field_index = 0;
            QTreeWidgetItem* item = new QTreeWidgetItem(ui->endpoint_tree->topLevelItem(index));
            for (int i =1; i<dict.toArray().size(); i++){
                item->setText(field_index, dict.toArray()[i].toString());
            }
            item->setData(0, Qt::UserRole + 1, QVariant(this->lastClickedDevice));
            index++;
        }
    }

}


void Dplm::endpointClicked(QTreeWidgetItem* item, int column)
{
    Q_UNUSED(column);
    if (item->childCount() > 0)
        return;
    int device_id = item->data(0, Qt::UserRole + 1).toInt();
    std::filesystem::path reqPath = "Dplm.postman_collection.json";
    http::RequestForm reqForm = http::readRequest(reqPath, "GetDevice");
    http::replace(reqForm.urlRaw, "$address", str(ui->hostName->text()));
    http::replace(reqForm.urlRaw, "$id", std::to_string(device_id));
    reqForm.setHeader("Authorization", this->authToken);
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
        reqForm.setHeader("Authorization", this->authToken);
        reqForm.setHeader("Host", str(ui->hostName->text()));
        http::replace(reqForm.body, "$clientID", str(clientID));
        http::replace(reqForm.body, "$endpoint", str(item->text(0)));
        executeRequest(reqForm.urlRaw,
                        reqForm.headers, reqForm.method);
        auto response = executeRequest(reqForm.urlRaw,
                                       reqForm.headers, reqForm.method);
        if (response.responseCode == 200){
            item->setText(1, response.resultString.c_str());
        }
    }

}
