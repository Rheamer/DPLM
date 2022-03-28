#include "dplm.h"
#include "python_utilities.h"
#include <QApplication>
#include <QDebug>
#include <QLocale>
#include <QTranslator>
#include <iostream>
#include "./ui_dplm.h"
#include <exception>


int main(int argc, char* argv[])
{
    QApplication a(argc, argv);
    Py_Initialize();
    auto* ui = new Ui::Dplm;
    Dplm* w = new Dplm(ui);
    w->setAttribute(Qt::WA_DeleteOnClose);
    w->show();
    int execSignal = 0;
    execSignal = a.exec();
    if (Py_FinalizeEx() < 0 )
        exit(120);
    std::cout << "Finished UsbConnect..." << std::endl;
    return execSignal;
}
