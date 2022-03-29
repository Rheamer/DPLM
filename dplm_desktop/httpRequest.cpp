#include "httpRequest.hpp"

#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <iostream>

std::string rawRequest(const std::string &resourceAddress,
                       const std::multimap<std::string, std::string> &headers)
{

    std::string domain, address;
    std::tie(domain, address) = http::splitDomain(resourceAddress);
    httplib::Client req(domain);
    req.enable_server_certificate_verification(false);
    httplib::Headers header(headers.begin(), headers.end());
    auto reply = req.Get(address.c_str(), header);
    if (reply.error() != httplib::Error::Success) {
        return "";
    }
    return reply->body;
}

RequestResult executeRequest(const std::string &resourceAddress,
                             const std::multimap<std::string, std::string> &headers,
                             const std::string &method,
                             const std::string &body,
                             const std::string &cookie)
{
    RequestResult requestResult;
    std::string domain, address;
    std::tie(domain, address) = http::splitDomain(resourceAddress);
    httplib::Client req(domain);
    req.enable_server_certificate_verification(false);
    auto header = httplib::Headers(headers.begin(), headers.end());
    if (!cookie.empty())
        header.insert({ "Cookie", cookie });
    httplib::Response reply;
    if (method == "GET") {
        auto res = req.Get(address.c_str(), header);
        if (res.error() != httplib::Error::Success) {
            requestResult.resultString = httplib::to_string(res.error());
            requestResult.responseCode = 0;
            std::cout << requestResult.resultString << '\n' << resourceAddress <<'\n';
            return requestResult;
        }
        reply = res.value();
    } else if (method == "POST") {
        auto res = req.Post(address.c_str(), header, body, "application/json");
        if (res.error() != httplib::Error::Success) {
            requestResult.resultString = httplib::to_string(res.error());
            requestResult.responseCode = 0;
            std::cout << requestResult.resultString << '\n' << resourceAddress <<'\n';
            return requestResult;
        }
        reply = res.value();
    }
    if (reply.status == 200) {
        requestResult.responseCode = reply.status;
        requestResult.resultString = reply.body;
        for (auto& pair : reply.headers)
            requestResult.headerFields[pair.first].push_back(pair.second);
    } else {
        std::cout << reply.reason;
        std::cout << reply.status;
        std::cout << reply.body << '\n';
        std::cout << "Original body: " << body << '\n';
        requestResult.responseCode = reply.status;
        requestResult.resultString = reply.reason;
    }
    return requestResult;
}

std::tuple<std::string, std::string> http::splitDomain(const std::string &source)
{
    int domainEnd = 0;
    int cnt = 0;
    for (int i = 0; i < source.length(); ++i)
        if (source[i] == '/')
            if (++cnt == 3) {
                domainEnd = i;
                break;
            }
    std::string domain = source.substr(0, domainEnd);
    std::string address = source.substr(domainEnd, source.size() - domainEnd);
    return { domain, address };
}

http::RequestForm http::readRequest(std::filesystem::path path, std::string requestName)
{
    QJsonDocument fileUnparsed;
    QJsonObject reqUnparsed;
    QFile reqFile((path).generic_string().c_str());
    reqFile.open(QIODevice::ReadOnly);
    fileUnparsed = QJsonDocument::fromJson(reqFile.readAll());
    for(auto item: fileUnparsed.object().find("item")->toArray()){
        if (item.toObject().find("name")->toString() == requestName.c_str()){
            reqUnparsed = item.toObject().find("request")->toObject();
        }
    }
    http::RequestForm request;
    request.urlRaw = reqUnparsed
            .find("url").value()
            .toObject().find("raw").value()
            .toString().toStdString();

    request.method = reqUnparsed
            .find("method").value()
            .toString().toStdString();

    for(auto header : reqUnparsed.find("header")->toArray()){
        request.headers.insert({
                    header.toObject().find("key").value().toString().toStdString(),
                    header.toObject().find("value").value().toString().toStdString()
                    });
    }

    request.body = reqUnparsed.find("body")
            .value().toObject().find("raw").value().toString().toStdString();

    return request;
}

bool http::replace(std::string &s, const std::string &from, const std::string &to)
{
    size_t start_pos = s.find(from);
    if(start_pos == std::string::npos)
        return false;
    s.replace(start_pos, from.length(), to);
    return true;
}

