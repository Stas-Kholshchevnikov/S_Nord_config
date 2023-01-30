import requests
import json
import os
import time
import datetime
from constants import validFormat, errorFormat


def check_ch(ch_box, *line_ed):
    """
    Функция отслеживания состояния активности полей для заполнения
    :param ch_box: чек-бокс
    :param line_ed: поля ввода
    :return:
    """
    if ch_box.isChecked():
        for item in line_ed:
            item.setEnabled(True)
    else:
        for item in line_ed:
            item.setEnabled(False)


def authorization(self):
    """
    Функция подключения к облаку и получения списка доступных объектов
    :param self:
    :return:
    """
    self.textEdit.setText(validFormat.format(""))
    self.textEdit_2.setText(errorFormat.format(""))
    self.progressBar.setEnabled(True)
    self.progressBar.setValue(0)
    time.sleep(0.1)
    self.textEdit.append(validFormat.format("Авторизация..."))
    self.progressBar.setValue(50)
    time.sleep(0.1)
    # Создаем сессию подключения и авторизуемся на сайте.
    # Создаем сессию для того чтобы при каждом дальнейшем запросе не авторизоваться.
    ses = requests.session()
    user_login = self.lineEdit_3.text()
    user_pass = self.lineEdit_4.text()
    user_data = {"email": user_login, "password": user_pass}
    answer = ses.post("https://keyboard.55-service.ru/login?next=%2F#/objects", json=user_data)
    if answer.status_code != 200:
        self.textEdit_2.append(errorFormat.format("Ошибка связи с сервером"))
        self.progressBar.setValue(100)
        self.progressBar.setEnabled(False)
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.pushButton_3.setEnabled(True)
        raise Exception

    # Полуение времени запроса обновления страницы с объектами. Нужно будет для дальнейшего формирования запроса
    time_request = time.time_ns()
    answer = ses.get("https://keyboard.55-service.ru/#/objects")

    # Откидываем 6 знаков с конца времени запроса, приводим к формату get запроса
    time_start = str(time_request)[:-6]
    answer = ses.get(f"https://keyboard.55-service.ru/objects?tm={time_start}")

    # Проверяем пройденность авторизации исходя из ответа полученного с сайта
    if "Please enter correct email." in answer.text:
        self.textEdit_2.append(errorFormat.format("Авторизация не пройдена"))
        self.progressBar.setValue(100)
        self.progressBar.setEnabled(False)
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.pushButton_3.setEnabled(True)
        raise Exception

    # Сохраняем скачанный перечень объектов в файл json
    with open("s-nord_list_of_object.json", "w", encoding="UTF-8") as file:
        file.write(answer.text)

    # Формируем из файла json словарь для python
    with open("s-nord_list_of_object.json", "r", encoding="UTF-8") as file:
        responce = json.loads(file.read())

    return responce, ses


def processing(self):
    """
    Функция обработки нажатия кнопки "Программировать"
    :param self:
    :return:
    """
    self.pushButton.setEnabled(False)
    self.pushButton_2.setEnabled(False)
    self.pushButton_3.setEnabled(False)
    setting_dict = {}
    try:
        responce, ses = authorization(self)
    except Exception:
        return

    # Загружаем из файла информацию о уже обработанных приборах
    with open(os.path.join("data", "all_devices.json"), "r", encoding="UTF-8") as file:
        setting_dict = json.loads(file.read())

    #Проверяем есть ли список доступных приборов
    if responce["permissions"]:
        self.textEdit.append(validFormat.format(f"Доступно приборов: {len(responce['permissions'])}"))
        self.progressBar.setValue(100)
        time.sleep(0.5)
    else:
        self.textEdit.append(validFormat.format("Список доступных приборов пуст"))
        self.progressBar.setValue(100)
        self.progressBar.setEnabled(False)
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.pushButton_3.setEnabled(True)
        return

    #Рассчитываем дельту для progressBar
    delta = round(99 / len(responce["permissions"]), 2)
    self.progressBar.setValue(0)
    count = 0
    #Создаем словарь для хранения старых и новых данных для формирования отчета
    change_data = {}
    change_list = []

    # Выделение из словаря адресов конфигурирования приборов и перебор их в for. Перебираем каждый прибор
    for item in range(len(responce["permissions"])):
        time.sleep(0.1)
        count += delta
        part_of_adress = responce["permissions"][item]["config_modes"]["configurator"]

        # Проверяем сконфигурирован ли прибор ранее. Если есть разрешение на перезапись, то проверка не выполняется
        if not self.checkBox_8.isChecked():
            if str(responce['permissions'][item]['object_number']) in setting_dict.keys():
                if setting_dict[str(responce['permissions'][item]['object_number'])] != "Ошибка загрузки!":
                    self.textEdit.append(validFormat.format(f"Прибор {responce['permissions'][item]['object_number']} уже сконфигурирован"))
                    self.progressBar.setValue(count)
                    continue

        #Сохраняем номер прибора
        change_data["object_number"] = responce['permissions'][item]['object_number']

        #Скачиваем файл конфигурации приборов и Дашборд
        try:
            device_number = responce['permissions'][item]['object_number']
            download_setting(part_of_adress, device_number, ses)
        except Exception:
            self.textEdit_2.append(errorFormat.format(f"{device_number} - Ошибка подключения!"))
            setting_dict[device_number] = "Ошибка загрузки!"
            self.progressBar.setValue(count)
            continue

        # Открываем json файл с настройками для замены данных
        with open(os.path.join("data", f"s-nord_{responce['permissions'][item]['object_number']}.json"), "r",
                  encoding="UTF-8") as file:
            setting = json.loads(file.read())


        # Проверяем на наличие возможности подключения внешней антены (для блоков B312)
        try:
            if setting['settings']['misc']['gsm_use_ext_ant'] in [0, 1]:
                setting['settings']['misc']['gsm_use_ext_ant'] = 1
                change_data['etx_ant'] = ['Включена поддержка внешней антены', 'Выкл', 'Вкл']
        except Exception:
            pass

        # Меняем данные настроек подключения к центру охраны по GPRS
        if self.checkBox.isChecked():
            change_data["channels_gprs_host_main"] = ["Основной адрес подключения к Центру охраны по GPRS", setting['settings']['channels']['gprs'][0]['host'], self.lineEdit.text()]
            change_data["channels_gprs_port_main"] = ["Основной порт подключения к Центру охраны по GPRS", setting['settings']['channels']['gprs'][0]['port'], self.lineEdit_2.text()]
            setting['settings']['channels']['gprs'][0]['host'] = self.lineEdit.text()
            setting['settings']['channels']['gprs'][0]['port'] = int(self.lineEdit_2.text())

        if self.checkBox_2.isChecked():
            change_data["channels_gprs_host_res"] = ["Резервный адрес подключения к Центру охраны по GPRS", setting['settings']['channels']['gprs'][1]['host'], self.lineEdit_5.text()]
            change_data["channels_gprs_port_res"] = ["Резервный порт подключения к Центру охраны по GPRS", setting['settings']['channels']['gprs'][1]['port'], self.lineEdit_6.text()]
            #change_data["channels_gprs_host_res"] = [1, '2', '3']
            setting['settings']['channels']['gprs'][1]['host'] = self.lineEdit_5.text()
            setting['settings']['channels']['gprs'][1]['port'] = int(self.lineEdit_6.text())

        # Если выбранное устройство банкомат, то меняем настройки Ethernet подключения к ЦО
        if self.checkBox_4.isChecked():
            if int(responce['permissions'][item]['object_number']) > 274999:
                #Проверяем не заполнен ли ранее эти параметры
                if setting['settings']['channels']['ethernet'][0]['host'] == "":
                    change_data["channels_eth_host_main"] = ["Основной адрес подключения к Центру охраны по Ethernet", setting['settings']['channels']['ethernet'][0]['host'], self.lineEdit_7.text()]
                    change_data["channels_eth_port_main"] = ["Основной порт подключения к Центру охраны по Ethernet", setting['settings']['channels']['ethernet'][0]['port'], self.lineEdit_10.text()]
                    setting['settings']['channels']['ethernet'][0]['host'] = self.lineEdit_7.text()
                    setting['settings']['channels']['ethernet'][0]['port'] = int(self.lineEdit_10.text())

        if self.checkBox_3.isChecked():
            if int(responce['permissions'][item]['object_number']) > 274999:
                # Проверяем не заполнен ли ранее эти параметры
                if setting['settings']['channels']['ethernet'][1]['host'] == "":
                    change_data["channels_eth_host_res"] = ["Резервный адрес подключения к Центру охраны по Ethernet", setting['settings']['channels']['ethernet'][1]['host'], self.lineEdit_8.text()]
                    change_data["channels_eth_port_res"] = ["Резервный порт подключения к Центру охраны по Ethernet", setting['settings']['channels']['ethernet'][1]['port'], self.lineEdit_9.text()]
                    setting['settings']['channels']['ethernet'][1]['host'] = self.lineEdit_8.text()
                    setting['settings']['channels']['ethernet'][1]['port'] = int(self.lineEdit_9.text())

        #Замена параметров подключения к облаку по GPRS
        if self.checkBox_5.isChecked():
            change_data["cloud_gprs_host"] = ["Адрес подключения к Облаку по GPRS", setting['settings']['cloud']['gprs']['host'], self.lineEdit_11.text()]
            change_data["cloud_gprs_port"] = ["Порт подключения к Облаку по GPRS", setting['settings']['cloud']['gprs']['port'], self.lineEdit_12.text()]
            setting['settings']['cloud']['gprs']['host'] = self.lineEdit_11.text()
            setting['settings']['cloud']['gprs']['port'] = int(self.lineEdit_12.text())

        # Замена параметров подключения к облаку по Ethernet
        if self.checkBox_6.isChecked():
            change_data["cloud_eth_host"] = ["Адрес подключения к Облаку по Ethernet", setting['settings']['cloud']['ethernet']['host'], self.lineEdit_13.text()]
            change_data["cloud_eth_port"] = ["Порт подключения к Облаку по Ethernet", setting['settings']['cloud']['ethernet']['port'], self.lineEdit_14.text()]
            setting['settings']['cloud']['ethernet']['host'] = self.lineEdit_13.text()
            setting['settings']['cloud']['ethernet']['port'] = int(self.lineEdit_14.text())

        # Устанавливаем параметры сотовых оператор
        if self.checkBox_7.isChecked():
            change_data["csp"] = ["Настройки сотовых операторов изменены на ЦСМОС", "не ЦСМОС", "ЦСМОС"]
            setting['settings']['csp'][0]['plmn'] = self.lineEdit_16.text()
            setting['settings']['csp'][0]['password'] = self.lineEdit_19.text()
            setting['settings']['csp'][0]['apn'] = self.lineEdit_17.text()
            setting['settings']['csp'][0]['name'] = self.lineEdit_15.text()
            setting['settings']['csp'][0]['user'] = self.lineEdit_18.text()
            setting['settings']['csp'][1]['plmn'] = self.lineEdit_20.text()
            setting['settings']['csp'][1]['password'] = self.lineEdit_24.text()
            setting['settings']['csp'][1]['apn'] = self.lineEdit_22.text()
            setting['settings']['csp'][1]['name'] = self.lineEdit_21.text()
            setting['settings']['csp'][1]['user'] = self.lineEdit_23.text()
            setting['settings']['csp'][2]['plmn'] = self.lineEdit_25.text()
            setting['settings']['csp'][2]['password'] = self.lineEdit_29.text()
            setting['settings']['csp'][2]['apn'] = self.lineEdit_27.text()
            setting['settings']['csp'][2]['name'] = self.lineEdit_26.text()
            setting['settings']['csp'][2]['user'] = self.lineEdit_28.text()
            setting['settings']['csp'][3]['plmn'] = self.lineEdit_32.text()
            setting['settings']['csp'][3]['password'] = self.lineEdit_31.text()
            setting['settings']['csp'][3]['apn'] = self.lineEdit_30.text()
            setting['settings']['csp'][3]['name'] = self.lineEdit_34.text()
            setting['settings']['csp'][3]['user'] = self.lineEdit_33.text()


        with open(os.path.join("data", f"s-nord_{responce['permissions'][item]['object_number']}_new.json"), "w",
                  encoding="UTF-8") as file:
            json.dump(setting, file, indent=4, ensure_ascii=False)

        # Загружаем новые данные в прибор
        try:
            setting_download = ses.post(f"https://keyboard.55-service.ru{part_of_adress}/settings", json=json.loads(
                open(os.path.join("data", f"s-nord_{responce['permissions'][item]['object_number']}_new.json"), "r",
                     encoding="UTF-8").read()))
        except Exception:
            self.textEdit_2.append(errorFormat.format(f"{responce['permissions'][item]['object_number']} - Ошибка загрузки!"))
            setting_dict[responce['permissions'][item]['object_number']] = "Ошибка загрузки!"
            self.progressBar.setValue(int(count))
            continue
        else:
            self.textEdit.append(validFormat.format(f"Данные в прибор {responce['permissions'][item]['object_number']} загружены!!!"))
            setting_dict[responce['permissions'][item]['object_number']] = datetime.datetime.now().strftime(
                "%d-%m-%Y %H.%M.%S")
            self.progressBar.setValue(int(count))

            #Добавляем в список словарь данных конкретного прибора
            change_list.append(change_data)
            change_data = {}

    self.progressBar.setValue(99)
    # Записываем в файл информацию о уже обработанных приборах
    with open(os.path.join("data", "all_devices.json"), "w", encoding="UTF-8") as file:
        json.dump(setting_dict, file, indent=4, ensure_ascii=False)

    #Формируем отчет о сессии
    report_name = str(datetime.datetime.now().strftime('%d-%m-%Y %H.%M.%S'))
    with open(os.path.join("reports", f"{report_name}.doc"), "w", encoding="UTF-8") as file:
        for item in range(len(change_list)):
            file.writelines(f"Объект: {change_list[item]['object_number']}\n")
            for key in change_list[item]:
                if key != "object_number":
                    file.writelines(f"{change_list[item][key][0]}\n")
                    file.writelines(f"Было: {change_list[item][key][1]}   ->  Стало: {change_list[item][key][2]}\n\n")
            file.writelines(f"----------------------------------------------------------\n\n")
    self.textEdit.append(validFormat.format(f"\nСформирован отчет: '{report_name}.doc'"))
    self.progressBar.setValue(100)
    self.progressBar.setEnabled(False)
    self.pushButton.setEnabled(True)
    self.pushButton_2.setEnabled(True)
    self.pushButton_3.setEnabled(True)

    # Отправка данных на прибор
    # ses.post(https://keyboard.55-service.ru/configurator/276056/5/7/20/8/settings, json=)


def download_setting(part_of_adress, device_number, ses, prefix=''):    # проверить на правильность вызова
    # Подключение к настройкам прибора
    time_request = time.time_ns()
    time_1 = str(time_request)[:-6]

    answer_setting = ses.get(f"https://keyboard.55-service.ru{part_of_adress}/settings?tm={time_1}")

    time_request = time.time_ns()
    time_2 = str(time_request)[:-6]

    answer_dashboard = ses.get(f"https://keyboard.55-service.ru{part_of_adress}/dashboard/?tm={time_2}")


    # Создаем отдельный файл с настройками для каждого прибора
    with open(os.path.join("data", f"s-nord_{device_number}{prefix}.json"), "w",
              encoding="UTF-8") as file:
        file.write(answer_setting.text)

    # Создаем отдельный файл с настройками Дашборда для каждого прибора
    with open(os.path.join("data", "dashboard", f"s-nord_{device_number}_dashboard.json"), "w",
              encoding="UTF-8") as file:
        file.write(answer_dashboard.text)
    return


def read_config(self):
    self.pushButton.setEnabled(False)
    self.pushButton_2.setEnabled(False)
    self.pushButton_3.setEnabled(False)
    try:
        responce, ses = authorization(self)
    except Exception:
        return

    # Проверяем есть ли список доступных приборов
    if responce["permissions"]:
        self.textEdit.append(validFormat.format(f"Доступно приборов: {len(responce['permissions'])}"))
        self.progressBar.setValue(100)
        time.sleep(0.5)
    else:
        self.textEdit.append(validFormat.format("Список доступных приборов пуст"))
        self.progressBar.setValue(100)
        self.progressBar.setEnabled(False)
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.pushButton_3.setEnabled(True)
        return

    # Рассчитываем дельту для progressBar
    delta = round(99 / len(responce["permissions"]), 2)
    self.progressBar.setValue(0)
    count = 0
    prefix = "_new"

    #Открываем файл со всеми приборами для добавления приборов после скачивания
    with open(os.path.join("data", "all_devices.json"), "r", encoding="UTF-8") as file:
        all_devices_dict = json.loads(file.read())

    # Выделение из словаря адресов конфигурирования приборов и перебор их в for. Перебираем каждый прибор
    for item in range(len(responce["permissions"])):
        time.sleep(0.1)
        count += delta
        part_of_adress = responce["permissions"][item]["config_modes"]["configurator"]

        # Скачиваем файл конфигурации приборов и Дашборд
        try:
            device_number = responce['permissions'][item]['object_number']

            download_setting(part_of_adress, device_number, ses, prefix)
            self.textEdit.append(validFormat.format(f"{device_number} - Конфигурации считаны!"))
            self.progressBar.setValue(int(count))
            all_devices_dict[device_number] = datetime.datetime.now().strftime("%d-%m-%Y %H.%M.%S")
        except Exception:
            self.textEdit_2.append(errorFormat.format(f"{device_number} - Ошибка подключения!"))
            self.progressBar.setValue(count)
            continue
        self.progressBar.setValue(int(count))


    # Записываем в файл информацию о уже обработанных приборах
    with open(os.path.join("data", "all_devices.json"), "w", encoding="UTF-8") as file:
        json.dump(all_devices_dict, file, indent=4, ensure_ascii=False)

    self.progressBar.setValue(100)
    self.progressBar.setEnabled(False)
    self.pushButton.setEnabled(True)
    self.pushButton_2.setEnabled(True)
    self.pushButton_3.setEnabled(True)


