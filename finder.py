#!/usr/bin/python3
# -*- coding: utf-8 -*-
import urllib
import config
import socks
import socket
import struct
import random
import requests
import time
import re
import netaddr
import logging
import bs4

from globaldata import ip_found
from globaldata import screen_queue
from globaldata import ip_ranges

# from screenshot import get_screenshot
from sockshandler import SocksiPyHandler

logging.basicConfig(level=config.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(name="Finder")

# билдер запросов для FTP
opener = urllib.request.build_opener(
    SocksiPyHandler(socks.PROXY_TYPE_SOCKS5, config.tor_host, config.tor_port)
)
urllib.request.install_opener(opener)

# regexp для извлечения заголовка
title_regex = re.compile(r'<title.*?>(.+?)</title>', re.IGNORECASE)

# ФУНКЦИИ РАНДОМИЗАЦИИ 


def get_random_web_port():
    # return 80
    # return random.choice([21,80])
    return random.choice(config.ports)


# абсолютно случайный IP
def get_fully_random_ip():
    # return "icanhazip.com" # screen test
    # return "193.43.36.131" # ftp test
    return str(socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff))))


# случайный IP из подгруженных диапазонов
def get_random_ip_from_ranges():
    return str(random.choice(random.choice(ip_ranges)))


# функция для получения случайного IP, может переключаться
get_random_ip = get_fully_random_ip


# загрузка диапазонов из файла
def load_ip_ranges(file):
    global get_random_ip
    total_ranges = 0
    try:
        ip_ranges.clear()
        with open(file, "r") as diaps:
            for line in diaps:
                try:
                    diap = line.split('-')
                    if len(diap) == 2:
                        ip_ranges.append(netaddr.IPRange(diap[0], diap[1]))
                    else:
                        ip_ranges.append(netaddr.IPNetwork(diap[0]))
                    
                    total_ranges += 1

                except Exception as e:
                    logger.error("Error while adding range {}: {}".format(line, e))
    except Exception as e:
        logger.error("Error while loading ranges from {} ({}), switched to fully random mode".format(file, e))
        get_random_ip = get_fully_random_ip

    return total_ranges


# ПОЛУЧЕНИЕ ДАННЫХ
def get_ftp_response(ip):
    result = "#FTP\n"
    try:
        response = urllib.request.urlopen("ftp://{}/".format(ip), timeout=config.http_wait).read()
        filelist = response.decode("utf-8").replace('\r', '').split("\n")[1:]

        for fileName in filelist[:-1]:
            result += '{}\n'.format(re.sub(' +', ' ', fileName).split(" ")[-1])
    except Exception:
        return None

    return result


def get_http_response(ip, port):
    result = None
    response = None

    try:
        response = requests.get('http://{}:{}/'.format(ip, port), timeout=config.http_wait, proxies=config.tor_proxy)

        text = response.text

        # pass in explicit encoding if set as a header
        encoding = response.encoding if 'charset' in response.headers.get('content-type', '').lower() else None
        content = response.content
        soup = bs4.BeautifulSoup(content, "html.parser", from_encoding=encoding)
        if soup.original_encoding != 'utf-8':
            meta = soup.select_one('meta[charset], meta[http-equiv="Content-Type"]')
            if meta:
                # replace the meta charset info before re-encoding
                if 'charset' in meta.attrs:
                    meta['charset'] = 'utf-8'
                else:
                    meta['content'] = 'text/html; charset=utf-8'
            # re-encode to UTF-8
            text = soup.prettify()  # encodes to UTF-8 by default

        # формируем текст сопроводительного сообщения
        # хэштег с кодом
        restext = "#code{}".format(response.status_code)

        # добавляем заголовок сервера в качестве хэштега 
        if 'Server' in response.headers:
            restext += " #{}".format(response.headers['Server'])

        # добавляем заголовок
        title = soup.select_one('title').string
        if title:
            title = title + "\n"
        else:
            title = ""

        # записываем текст в result
        result = restext + "\n" + title

        # ФИЛЬТРАЦИЯ РЕЗУЛЬТАТОВ
        # по-хорошему, надо вынести в конфиг или отдельный файл

        # пропускаем Akamai
        if response.status_code in [400, 403] \
                and "Server" in response.headers \
                and response.headers["Server"] == "AkamaiGHost" \
                and "<H1>Invalid URL</H1>" in   text:
            result = None
        # пропускаем всё что требует авторизации на уровне браузера
        elif response.status_code == 401:
            result = None
        # пропускаем Cloudflare 1003
        # elif (response.status_code == 403 and
        #     "Server" in response.headers and
        #     response.headers["Server"] == "cloudflare-nginx" and 
        #     "Direct IP access not allowed | Cloudflare" in response.text):
        #     result = None
        # пропускаем всё что заявляет о недостаточных правах

    except Exception as e:
        logger.debug("Scan thread error: {}".format(e))
        pass

    finally:
        if response:
            response.close()

    return result


# цикл поиска
def ipsearch():
    try:
        # print("Worker start...")
        while True:
            while ip_found.qsize() > config.max_ip_pool-1:
                time.sleep(1)

            ip = get_random_ip()
            port = get_random_web_port()

            # logger.debug("IP search: {}:{}...".format(ip, port))

            try:
                if port == 21:
                    data = get_ftp_response(ip)
                else:
                    data = get_http_response(ip, 80)

                if data:
                    logger.info("IP found: {}:{}".format(ip, port))
                    # помещаем данные в очередь скриншотинг
                    screen_queue.put((ip, port, data))

            except Exception as e:
                logger.error("Worker error: {}".format(e))

    except Exception as e:
        logger.error("Thread error: {}".format(e))
        return
