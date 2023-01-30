import json
import os
import datetime
import openpyxl
from constants import validFormat, errorFormat


def full_report(self):
    """
    Функция создания полного отчета
    :param self:
    :return:
    """
    self.textEdit.setText(validFormat.format(""))
    self.textEdit_2.setText(errorFormat.format(""))
    self.textEdit.append(validFormat.format(f"Формируется полный отчет"))
    self.progressBar.setEnabled(True)

    data = {}

    # Открываем файл с уже запрограммированными приборами
    with open(os.path.join("data", "all_devices.json"), "r", encoding="UTF-8") as file:
        setting_dict = json.loads(file.read())

    # Данные для трекбара
    delta = round(99 / len(setting_dict), 2)
    self.progressBar.setValue(0)
    count = 0

    for number_device, status in setting_dict.items():
        try:
            with open(os.path.join("data", f"s-nord_{number_device}_new.json"), "r", encoding="UTF-8") as file:
                setting = json.loads(file.read())
        except Exception:
            continue

        # Формируем переменные для дальнейшего словаря
        sc_gprs_host_1 = setting['settings']['channels']['gprs'][0]['host']
        sc_gprs_port_1 = setting['settings']['channels']['gprs'][0]['port']
        sc_gprs_host_2 = setting['settings']['channels']['gprs'][1]['host']
        sc_gprs_port_2 = setting['settings']['channels']['gprs'][1]['port']
        sc_eth_host_1 = setting['settings']['channels']['ethernet'][0]['host']
        sc_eth_port_1 = setting['settings']['channels']['ethernet'][0]['port']
        sc_eth_host_2 = setting['settings']['channels']['ethernet'][1]['host']
        sc_eth_port_2 = setting['settings']['channels']['ethernet'][1]['port']
        cl_gprs_host_1 = setting['settings']['cloud']['gprs']['host']
        cl_gprs_port_1 = setting['settings']['cloud']['gprs']['port']
        cl_eth_host_1 = setting['settings']['cloud']['ethernet']['host']
        cl_eth_port_1 = setting['settings']['cloud']['ethernet']['port']

        # Проверка на ЦСМОС (если есть хоть одна подходящая точка доступа)
        csmos = "Нет"
        for i in range(4):
            if setting['settings']['csp'][i]['apn'] in ["ops-sber.megafon.ru", "opssber.msk", "sec.ops.sberbank",
                                                        "opssber.beeline.ru"]:
                csmos = "Да"

        # Проверка на внешнюю антенну
        ext_ant = "Нет данных"
        try:
            if setting['settings']['misc']['gsm_use_ext_ant'] == 0:
                ext_ant = "Нет"
            else:
                ext_ant = "Да"
        except Exception:
            pass

        # Получение MAC адреса
        ip_addr = "Нет LAN модуля"
        mac = "Нет MAC адреса"
        try:
            if setting['settings']['ethernet']['ip_addr'] != "0.0.0.0":
                ip_addr = setting['settings']['ethernet']['ip_addr']
                mac_list = setting['settings']['ethernet']['mac']
                mac = " : ".join([hex(i) for i in mac_list])
        except Exception:
            pass

        # Попытка открыть файл конфигурации с Дашбордом
        plmn1 = ""
        plmn2 = ""
        try:
            with open(os.path.join("data", "dashboard", f"s-nord_{number_device}_dashboard.json"), "r",
                      encoding="UTF-8") as file:
                setting_dashboards = json.loads(file.read())
                plmn1 = setting_dashboards["sim1"]["plmn"]
                plmn2 = setting_dashboards["sim2"]["plmn"]
        except Exception:
            pass

        if plmn1 is None:
            plmn1 = ""
        if plmn2 is None:
            plmn2 = ""

        operator_sim1 = "Нет данных"
        sim1 = "Нет данных"
        operator_sim2 = "Нет данных"
        sim2 = "Нет данных"

        if (len(plmn1) > 11):
            operator_sim1 = plmn1[:5]
            sim1 = plmn1[5:]
        if (len(plmn2) > 11):
            operator_sim2 = plmn2[:5]
            sim2 = plmn2[5:]

        # Формирование словаря данных по конкретному прибору
        data[number_device] = {
            "sc_gprs_host_1": sc_gprs_host_1,
            "sc_gprs_port_1": sc_gprs_port_1,
            "sc_gprs_host_2": sc_gprs_host_2,
            "sc_gprs_port_2": sc_gprs_port_2,
            "sc_eth_host_1": sc_eth_host_1,
            "sc_eth_port_1": sc_eth_port_1,
            "sc_eth_host_2": sc_eth_host_2,
            "sc_eth_port_2": sc_eth_port_2,
            "cl_gprs_host_1": cl_gprs_host_1,
            "cl_gprs_port_1": cl_gprs_port_1,
            "cl_eth_host_1": cl_eth_host_1,
            "cl_eth_port_1": cl_eth_port_1,
            "csmos": csmos,
            "ext_ant": ext_ant,
            "ip_addr": ip_addr,
            "mac": mac,
            "operator_sim1": operator_sim1,
            "sim1": sim1,
            "operator_sim2": operator_sim2,
            "sim2": sim2
        }
        count += delta
        self.progressBar.setValue(int(count))

    create_excel_report(self, data)
    self.progressBar.setValue(100)
    self.progressBar.setEnabled(False)


def create_excel_report(self, data):
    """
    Функция создания файла Excel отчета
    :param self:
    :param data:
    :return:
    """
    book = openpyxl.Workbook()
    sheet = book.active

    sheet['B2'].value = "Номер объекта"
    sheet['C2'].value = "IP-адрес №1(GPRS) подключения к центру охраны"
    sheet['D2'].value = "Порт №1(GPRS) подключения к центру охраны"
    sheet['E2'].value = "IP-адрес №2(GPRS) подключения к центру охраны"
    sheet['F2'].value = "Порт №2(GPRS) подключения к центру охраны"
    sheet['G2'].value = "IP-адрес №1(Ethernet) подключения к центру охраны"
    sheet['H2'].value = "Порт №1(Ethernet) подключения к центру охраны"
    sheet['I2'].value = "IP-адрес №2(Ethernet) подключения к центру охраны"
    sheet['J2'].value = "Порт №2(Ethernet) подключения к центру охраны"
    sheet['K2'].value = "IP-адрес (GPRS) подключения к облаку"
    sheet['L2'].value = "Порт (GPRS) подключения к облаку"
    sheet['M2'].value = "IP-адрес (Ethernet) подключения к облаку"
    sheet['N2'].value = "Порт (Ethernet) подключения к облаку"
    sheet['O2'].value = "ЦСМОС"
    sheet['P2'].value = "Разрешение подключения внешней антенны"
    sheet['Q2'].value = "IP-адрес LAN-модуля"
    sheet['R2'].value = "MAC-адресс LAN-модуля"
    sheet['S2'].value = "Оператор sim1"
    sheet['T2'].value = "ICCD sim1"
    sheet['U2'].value = "Оператор sim2"
    sheet['V2'].value = "ICCD sim2"

    i = 3
    for key in data.keys():
        sheet['B' + str(i)].value = key
        sheet['C' + str(i)].value = data[key]["sc_gprs_host_1"]
        sheet['D' + str(i)].value = data[key]["sc_gprs_port_1"]
        sheet['E' + str(i)].value = data[key]["sc_gprs_host_2"]
        sheet['F' + str(i)].value = data[key]["sc_gprs_port_2"]
        sheet['G' + str(i)].value = data[key]["sc_eth_host_1"]
        sheet['H' + str(i)].value = data[key]["sc_eth_port_1"]
        sheet['I' + str(i)].value = data[key]["sc_eth_host_2"]
        sheet['J' + str(i)].value = data[key]["sc_eth_port_2"]
        sheet['K' + str(i)].value = data[key]["cl_gprs_host_1"]
        sheet['L' + str(i)].value = data[key]["cl_gprs_port_1"]
        sheet['M' + str(i)].value = data[key]["cl_eth_host_1"]
        sheet['N' + str(i)].value = data[key]["cl_eth_port_1"]
        sheet['O' + str(i)].value = data[key]["csmos"]
        sheet['P' + str(i)].value = data[key]["ext_ant"]
        sheet['Q' + str(i)].value = data[key]["ip_addr"]
        sheet['R' + str(i)].value = data[key]["mac"]
        sheet['S' + str(i)].value = data[key]["operator_sim1"]
        sheet['T' + str(i)].value = data[key]["sim1"]
        sheet['U' + str(i)].value = data[key]["operator_sim2"]
        sheet['V' + str(i)].value = data[key]["sim2"]
        i += 1

    report_name = str(datetime.datetime.now().strftime('%d-%m-%Y %H.%M'))
    book.save(os.path.join("reports", "excel_reports", f"{report_name}.xlsx"))
    book.close()
    self.textEdit.append(validFormat.format(f"Сформирован отчет: {report_name}.xlsx"))
