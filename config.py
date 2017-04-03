#!/usr/bin/python3
# -*- coding: utf-8 -*-
# режим отладки. при установке в True будет использован другой бот и параметры (см. ниже)
import os
import logging

DEBUG = os.environ["PYDEBUG"]=="1" if "PYDEBUG" in os.environ else False

log_level = logging.INFO if DEBUG else logging.INFO

# настройки Tor
tor_host = "127.0.0.1"
tor_port = "9150"
tor_proxy = {'http': 'socks5://{}:{}'.format(tor_host, tor_port)}

# список портов для сканирования
ports = [21, 80, 81, 82, 83, 8000, 8080, 8081, 9000, 9080]

# количество адресов-результатов в пуле
max_ip_pool = 1000
# количество тредов для скана
max_search_threads = 700
# количество тредов для снятия скринов
max_screen_threads = 10

# задержка ожидания ответа по http
http_wait = 30
# задержка ожидания загрузки страницы для скриншотинга
screen_wait = 30
# задержка ожидания отработки скриптов для скриншотинга
screen_script_wait = 60
# пауза перед скриншотингом
screen_pause = 10
# размеры снимаемых скриншотов
screen_width = 1366
screen_height = 768

# заголовок http-запроса
http_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

# директория для храния скриншотов
screen_folder = "screens"

# путь к phantomjs (для скриншотинга)
phantomjs_path = '/usr/bin/phantomjs'

# ник администратора в телеграме
admin_username = 'pantene'

# список контактов (конференции, пользователи, каналы) для автоматической рассылки
chats = ['netstalking_screenshots']
# интервал рассылки
posting_wait = 60
# включение автоматической рассылки
autoposting = True

# директория с текстовыми файлами, содержащими диапазоны IP (простые, CIDR)
ranges_folder = "ranges"

# файл с диапазонами, загружаемый по умолчанию
# оставить пустым для скана по рандому
range_file = ""

# файл с заданиями
task_file = "tasks.json"

# для боевого режима
if not DEBUG:
    print("Loading prod config...")
    token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
# для режима отладки
else:
    print("Loadind debug config...")
    token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    max_search_threads = 10
    max_screen_threads = 10
    chats = []
    range_file = ""