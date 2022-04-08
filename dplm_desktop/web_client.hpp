#ifndef WEBCLIENT_HPP
#define WEBCLIENT_HPP

#include "./ui_login.h"
#include <QWidget>
#include "httpRequest.hpp"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QPushButton>
#include <string>
#include <map>

QT_BEGIN_NAMESPACE
namespace Ui {
class WebDialog;
}
QT_END_NAMESPACE

class WebClientInterface : public QObject {
    Q_OBJECT
private:
    std::unique_ptr<QDialog> loginPopup;
    std::unique_ptr<Ui::WebDialog> uiPopup;
    std::string webLoginEntered;
    std::string webPassEntered;
    std::string webIpEntered;
    std::string webPortEntered;
    inline static std::string userPass;
    QAbstractButton* hiddenServerAccessButton;
    std::string token;

    inline void setupConnections()
    {
        connect(uiPopup->btnBox, &QDialogButtonBox::accepted,
            this, [=]() {
            Q_EMIT accepted(
                        this->webLoginEntered,
                        uiPopup->ip->text().toStdString(),
                        uiPopup->port->text().toStdString(),
                        this->token);
        });
        connect(uiPopup->authBtn, &QPushButton::released,
                this, &WebClientInterface::authenticate);
        connect(this, &WebClientInterface::webAuthFailS,
                this, &WebClientInterface::webAuthFail,
                Qt::QueuedConnection);
        connect(this, &WebClientInterface::webAuthSuccessS,
                this, &WebClientInterface::webAuthSuccess,
                Qt::QueuedConnection);

        connect(uiPopup->registerUserBtn, &QPushButton::released,
                this, &WebClientInterface::registrate);
        connect(this, &WebClientInterface::webRegFailS,
                this, &WebClientInterface::webRegFail,
                Qt::QueuedConnection);
        connect(this, &WebClientInterface::webRegSuccessS,
                this, &WebClientInterface::webRegSuccess,
                Qt::QueuedConnection);
    }

Q_SIGNALS:
    // 'S' means method is used for async requests
    void webAuthFailS();
    void webAuthSuccessS();
    void webRegFailS();
    void webRegSuccessS();

    void accepted(std::string, std::string, std::string, std::string);

public:
    WebClientInterface()
        : loginPopup(std::make_unique<QDialog>())
        , uiPopup(std::make_unique<Ui::WebDialog>())
    {
        uiPopup->setupUi(loginPopup.get());
        setupConnections();
        hiddenServerAccessButton = uiPopup->btnBox->buttons().at(0);
        uiPopup->btnBox->removeButton(hiddenServerAccessButton);
    }

    void webUnsetIndication() Q_SLOT
    {
        uiPopup->authIcon->setIcon(QIcon());
        uiPopup->addressIcon->setIcon(QIcon());
    }

    void authenticate()
    {
        if (uiPopup->authBtn->isFlat())
            return;
        uiPopup->authBtn->setEnabled(false);
        uiPopup->authBtn->setFlat(true);
        this->webUnsetIndication();
        this->webLoginEntered = uiPopup->login->text().toStdString();
        this->webPassEntered = uiPopup->password->text().toStdString();
        this->webIpEntered = uiPopup->ip->text().toStdString();
        this->webPortEntered = uiPopup->port->text().toStdString();
        const auto f = [=](){
            std::filesystem::path reqPath = "Dplm.postman_collection.json";
            http::RequestForm reqForm = http::readRequest(reqPath, "GetToken");
            std::string address = this->webIpEntered;
            if (this->webPortEntered != ""){
                address = address + ':' + this->webPortEntered;
            }
            http::replace(reqForm.urlRaw, "$address", address);
            http::replace(reqForm.body, "$username", this->webLoginEntered);
            http::replace(reqForm.body, "$password", this->webPassEntered);
            reqForm.setHeader("Host", address);
            auto response = executeRequest(reqForm.urlRaw,
                                           reqForm.headers, reqForm.method,
                                           reqForm.body);
            if (response.responseCode == 200){
                QJsonDocument body;
                body = QJsonDocument::fromJson(response.resultString.c_str());
                auto res = body.object();
                this->token = res.find("auth_token").value().toString().toStdString();
                Q_EMIT webAuthSuccessS();
            } else {
                Q_EMIT webAuthFailS();
            }
        };
        std::thread(f).detach();
    }


    void webAuthFail() Q_SLOT
    {
        uiPopup->authBtn->setEnabled(true);
        uiPopup->authBtn->setFlat(false);
        uiPopup->authIcon->setIcon(QIcon("./icons/fail.png"));
        std::cout << "Auth failed\n";
    }

    void webAuthSuccess() Q_SLOT
    {
        uiPopup->authBtn->setEnabled(true);
        uiPopup->authBtn->setFlat(false);
        uiPopup->authIcon->setIcon(QIcon("./icons/success.png"));
        uiPopup->addressIcon->setIcon(QIcon("./icons/success.png"));
        userPass = uiPopup->password->text().toStdString();
        uiPopup->creationStatus->setText("");
        uiPopup->btnBox->addButton(hiddenServerAccessButton,
            QDialogButtonBox::ButtonRole::AcceptRole);
    }

    void registrate()
    {
        if (uiPopup->registerUserBtn->isFlat())
            return;
        uiPopup->registerUserBtn->setEnabled(false);
        uiPopup->registerUserBtn->setFlat(true);
        this->webLoginEntered = uiPopup->newUsername->text().toStdString();
        this->webPassEntered = uiPopup->newPassword->text().toStdString();
        this->webIpEntered = uiPopup->ip->text().toStdString();
        this->webPortEntered = uiPopup->port->text().toStdString();
        const auto f = [=](){
            std::filesystem::path reqPath = "Dplm.postman_collection.json";
            http::RequestForm reqForm = http::readRequest(reqPath, "CreateUser");
            std::string address = this->webIpEntered;
            if (this->webPortEntered != ""){
                address = address + ':' + this->webPortEntered;
            }
            http::replace(reqForm.urlRaw, "$address", address);
            http::replace(reqForm.body, "$username", this->webLoginEntered);
            http::replace(reqForm.body, "$password", this->webPassEntered);
            http::replace(reqForm.body, "$re_password", this->webPassEntered);
            reqForm.setHeader("Host", address);
            auto response = executeRequest(reqForm.urlRaw,
                                           reqForm.headers, reqForm.method,
                                           reqForm.body);
            if (response.responseCode == 200){
                Q_EMIT webRegSuccessS();
            } else {
                Q_EMIT webRegFailS();
            }
        };
        std::thread(f).detach();
    }

    void webRegSuccess(){
        uiPopup->registerUserBtn->setEnabled(true);
        uiPopup->registerUserBtn->setFlat(false);
        userPass = uiPopup->newPassword->text().toStdString();
        uiPopup->creationStatus->setText("");
    }

    void webRegFail(){
        uiPopup->registerUserBtn->setEnabled(true);
        uiPopup->registerUserBtn->setFlat(false);
        uiPopup->creationStatus->setText("Registration failed");
    }

    void showClientWindow() Q_SLOT
    {
        uiPopup->authIcon->setIcon(QIcon());
        uiPopup->addressIcon->setIcon(QIcon());
        loginPopup->exec();
    }

    std::map<std::string, std::string> getAccessVariables()
    {
        std::map<std::string, std::string> retdict;
        retdict["username"] = this->webLoginEntered;
        retdict["password"] = this->webPassEntered;
        retdict["url"] = this->webIpEntered;
        retdict["port"] = this->webPortEntered;
        return retdict;
    }

};

#endif // WEBCLIENT_HPP
