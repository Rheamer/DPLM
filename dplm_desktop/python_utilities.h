#ifndef PYTHON_UTILITIES_H
#define PYTHON_UTILITIES_H

#include "Python.h"
#include <vector>
#include <memory>
#include <string>
#include <vector>
#include <unordered_map>


class PyUtils{
private:
    inline static std::unordered_map<std::string, PyObject*> loadedModules;

protected:

    std::vector<std::shared_ptr<char>> argConvert(std::string s, int& argc)
    {
        std::string delim = " ";
        size_t pos = 0;
        std::vector<std::string> args;
        while ((pos = s.find(delim)) != std::string::npos) {
            args.push_back(s.substr(0, pos));
            s.erase(0, pos + delim.length());
        }
        if (s.size() > 0)
            args.push_back(s);
        argc = args.size();
        std::vector<std::shared_ptr<char>> cstrings;
        cstrings.reserve(args.size());
        for (size_t i = 0; i < args.size(); ++i) {
            std::shared_ptr<char> c(new char[strlen(args[i].c_str()) + 1], std::default_delete<char[]>());
            strcpy(c.get(), args[i].c_str());
            cstrings.push_back(c);
        }
        return cstrings;
    }

public:
    /** Deprecated, script initialization is automated in runLine() */
    void init(std::string scriptName, std::string args)
    {
        if (!Py_IsInitialized())
            return;
        int argc;
        auto argvPts = argConvert(scriptName + args, argc);
        wchar_t** argv = (wchar_t**)PyMem_Malloc(sizeof(wchar_t*) * (argc + 1));
        for (int i = 0; i < argc; i++) {
            wchar_t* arg = Py_DecodeLocale(argvPts[i].get(), NULL);
            argv[i] = arg;
        }
        Py_SetProgramName(argv[0]);
        PySys_SetArgv(argc, argv);
        PyObject* obj = Py_BuildValue("s", scriptName.data());
        FILE* file = _Py_fopen_obj(obj, "r+");
        PyRun_SimpleFile(file, scriptName.data());
        PyMem_RawFree(argv);
        PyObject_Free(obj);
        fclose(file);
    }

    void runLine(const std::string& s)
    {
        if (Py_IsInitialized())
            PyRun_SimpleString(s.data());
    }

    std::string strFunc(std::string scriptName,
                        std::string funcName = "",
                        std::string args = "")
    {
        auto moduleIt = loadedModules.find(scriptName);
        PyObject *module,*func, *prm, *ret;
        if (moduleIt == loadedModules.end()){
            module = PyImport_ImportModule(scriptName.data());
            if (module != nullptr)
                loadedModules[scriptName] = module;
        } else {
            module = moduleIt->second;
        }
        std::string res;
        if (funcName != ""){
            if (module != 0) {
                func = PyObject_GetAttrString(module, funcName.data());
                PyErr_Print();
                prm = Py_BuildValue("(z)", args.data());
                PyErr_Print();
                ret = PyObject_CallObject(func, prm);
                PyErr_Print();
                Py_DECREF(prm);
                res = PyUnicode_AsUTF8(ret);
                Py_DECREF(ret);
            } else
                return "";
            return res;
        }
        return "";
    }
};
#endif // PYTHON_UTILITIES_H
