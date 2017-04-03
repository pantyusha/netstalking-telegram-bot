#!/usr/bin/python3
# -*- coding: utf-8 -*-
import config
import telebot
import finder
import screenshot
import tasks

import os
import sys
import time
import logging
import threading
import traceback

import GeoIP

from globaldata import ip_found

logging.basicConfig(level=config.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(name="Bot")

logger.info("Bot starting...")
bot = telebot.TeleBot(config.token, threaded=False)


# главная функция постинга результатов в чат
def post_to_chat(chat_id, initiator):
    # берём кортеж из IP, порта и текстовой информации из очереди
    ip, port, data = ip_found.get()
    ip_found.task_done()

    # определяем название файла скриншота
    img_filename = os.path.join(config.screen_folder, '{}_{}.png'.format(ip, port))

    logger.debug(data)

    # вытаскиваем геоданные по IP
    geoinfo = ""
    geodata = gi.record_by_name(ip)
    if geodata:
        if 'country_code3' in geodata and geodata['country_code3']:
            geoinfo += "\nCountry: {}".format(geodata['country_code3'])
        if 'city' in geodata and geodata['city']:
            geoinfo += "\nCity: {}".format(geodata['city'])

    # формируем правильную ссылку в зависимости от порта
    if port == 21:
        link = "ftp://{}/".format(ip)
    else:
        link = "http://{}:{}/".format(ip, port)

    # формируем конечное сообщение
    address_info = "{}{}{}".format(data, link, geoinfo)   

    # если есть скриншот, то отправляем сообщение с ним
    if os.path.exists(img_filename):
        logger.info("Send random IP with image {}:{} to {}".format(ip, port, initiator))
    
        bot.send_chat_action(chat_id, 'upload_photo')

        img = open(img_filename, 'rb')
        bot.send_photo(chat_id, img, caption="{}:{}".format(ip, port))
        img.close()
    else:
        logger.info("Send random IP {}:{} to {}".format(ip, port, initiator))
    
    bot.send_message(chat_id, address_info)


# функция N-минутной отправки результатов по данным сообщения
def results_sender_thread(message, interval):
    while True:
        time.sleep(60*interval)
        get_ip(message)


# функция регулярной отправки результатов по данным конфига 
def regular_posting():
    while True:
        time.sleep(config.posting_wait)
        
        while ip_found.qsize() == 0:
            time.sleep(config.screen_wait+config.screen_pause)

        for chat in config.chats: 
            try:
                post_to_chat("@"+chat, chat)
            except Exception as e:
                logger.error("Error while posting to {}: {}".format(chat, e))


# функция загрузки диапазонов из файла
def load_ranges_from_file(filename):
    count = finder.load_ip_ranges(os.path.join(config.ranges_folder, filename))
    if count:
        logger.info("Loaded {} ranges from {}, scanning by ranges mode enabled".format(count, config.range_file))
        finder.get_random_ip = finder.get_random_ip_from_ranges
        return count


# получение случайного нетсталкинг-задания
# нет аргументов
@bot.message_handler(commands=["roll"])
def task_exec(message):
    bot.send_message(message.chat.id, tasks.get_task())


# отправка результатов каждые N минут в чат
# только для админа
# 1 аргумент - количество минут - 1
@bot.message_handler(commands=["get_ip_every"])
def get_ip_every(message):
    args = message.text.split(" ")
    if message.from_user.username == config.admin_username:
        if len(args) == 2:
            bot.send_message(message.chat.id, "I will send scan results every {} min".format(args[1]))
            minutes = int(args[1])
            th = threading.Thread(target=results_sender_thread, args=(message, minutes))
            th.daemon = True
            th.start()
        else:
            bot.send_message(message.chat.id,
                             "Don't understand... send me count of minutes",
                             reply_to_message_id=message.message_id)


# получение информации о количестве результатов в очереди
# нет аргументов
@bot.message_handler(commands=["status"])
def get_scanned_count(message):
    bot.send_message(message.chat.id,
                     "Scanned IP in queue: {}".format(ip_found.qsize()),
                     reply_to_message_id=message.message_id)


# получение 20 результатов
# нет аргументов
@bot.message_handler(commands=["get_20_ip"])
def get_20_ip(message):
    counter = 20
    while counter > 0 and get_ip(message):
        counter -= 1


# получение 1 результата. присылается 2 сообщения: скрин сайта (если есть) и описание 
# нет аргументов
@bot.message_handler(commands=["get_ip"])
def get_ip(message):
    if ip_found.qsize() == 0:
        bot.send_message(message.chat.id, "Sorry, no stuff now! Please check again later!")
        return False
    else:
        post_to_chat(message.chat.id, message.from_user.username)
        return True


# переключение на сканирования диапазонов из файла
# 1 аргумент 
@bot.message_handler(commands=["scan_from_file"])
def scan_from_file(message):
    if message.from_user.username == config.admin_username:
        args = message.text.split(" ")
        if len(args) == 2:
            count = load_ranges_from_file(args[1])
            if count:
                bot.send_message(message.chat.id,
                                 "Loaded {} ranges from {}, scanning by ranges mode enabled".format(count, args[1]),
                                 reply_to_message_id=message.message_id)
            else:
                bot.send_message(message.chat.id,
                                 "Error while loading ranges from {}, switched to fully random mode".format(args[1]),
                                 reply_to_message_id=message.message_id)
            
        else:
            bot.send_message(message.chat.id, "Specify name of file with ranges!",
                             reply_to_message_id=message.message_id)
    else:
        bot.send_message(message.chat.id, "Sorry, this can do Master shampoo only!",
                         reply_to_message_id=message.message_id)


# переключение на сканирования диапазонов по полному рандому
# нет аргументов
@bot.message_handler(commands=["scan_random"])
def scan_random(message):
    if message.from_user.username == config.admin_username:
        finder.get_random_ip = finder.get_fully_random_ip
        bot.send_message(message.chat.id, "Fully random scanning mode enabled")
    else:
        bot.send_message(message.chat.id, "Sorry, this can do Master shampoo only!",
                         reply_to_message_id=message.message_id)


# очистка результатов
# нет аргументов
@bot.message_handler(commands=["clear_results"])
def scan_random(message):
    if message.from_user.username == config.admin_username:
        with ip_found.mutex:
            ip_found.queue.clear()
        bot.send_message(message.chat.id, "Results queue cleared!")
        logger.info("Results queue cleared!")
    else:
        bot.send_message(message.chat.id, "Sorry, this can do Master shampoo only!",
                         reply_to_message_id=message.message_id)


@bot.message_handler(content_types=["text"])
def hello_shampoo(message):
    text = message.text.lower()  
    if "шампун" in text or "пантин" in text or "pantene" in text:
        bot.send_message(message.chat.id, "Хоп хей лалалей!")


if __name__ == '__main__':

    logger.info("Data preloading...")
    gi = GeoIP.open("GeoLiteCity.dat", GeoIP.GEOIP_INDEX_CACHE | GeoIP.GEOIP_CHECK_CACHE)
    tasks.load()

    logger.info("Start threads generation...")
    # загружаем диапазоны для сканирования, если указаны в конфиге
    # можно вручную изменить командой /scan_from_file <название файла>
    # файл должен лежать в папке ranges_folder (по умолчанию ranges)
    if config.range_file != "":
        load_ranges_from_file(config.range_file)
    else:
        logger.info("Fully random scanning mode enabled")

    # запускаем потоки сканирования
    for _ in range(config.max_search_threads):
        t = threading.Thread(target=finder.ipsearch)
        t.daemon = True
        t.start()
    
    # запускаем потоки скриншотинга
    for _ in range(config.max_screen_threads):
        t = threading.Thread(target=screenshot.screener)
        t.daemon = True
        t.start()

    # включаем при необходимости автопостинг (нет, отключить пока нельзя)
    if config.autoposting and len(config.chats): 
        logger.info("Autoposting enabled for {}".format(", ".join(config.chats)))
        t = threading.Thread(target=regular_posting)
        t.daemon = True
        t.start()

    # магия с циклом для бесконечного переподключения и выхода по Ctrl+C
    # почему не вебхук? просто нахуй, ок?
    no_exit = True
    while no_exit:
        try:
            logger.info("YA RODILSYA!!!")
            bot.polling(none_stop=True, interval=1)        
            
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            logger.error(e)
            logger.error("Manually closed!")
            no_exit = False
            sys.exit(0)
