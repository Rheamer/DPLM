#ifndef HTTPREQUEST_HPP
#define HTTPREQUEST_HPP

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#endif
#define CPPHTTPLIB_OPENSSL_SUPPORT
#include <httplib.h>

#include <QString>
#include <QUuid>
#include <QStringList>
#include <QFile>
#include <filesystem>


namespace http {

struct RequestForm {
    void setHeader(std::string key, std::string value)
    {
        if (headers.find(key) != headers.end())
            headers.find(key)->second = value;
        else
            headers.insert({ key, value });
    }
    std::string method;
    std::string urlRaw;
    std::multimap<std::string, std::string> headers;
    std::string body;
};

std::tuple<std::string, std::string> splitDomain(std::string const& source);

RequestForm readRequest(std::filesystem::path, std::string requestName);
bool replace(std::string& s, const std::string& from, const std::string& to);
} //namespace http

struct RequestResult {
    std::string resultString = "";
    int responseCode = 200;
    std::unordered_map<std::string, std::vector<std::string>> headerFields;
};


RequestResult executeRequest(
    const std::string& resourceAddress,
    const std::multimap<std::string, std::string>& headers,
    const std::string& method,
    const std::string& body = "",
    const std::string& cookie = "");


std::string rawRequest(
    const std::string& resourceAddress,
    const std::multimap<std::string, std::string>& headers);

#endif // HTTPREQUEST_HPP
