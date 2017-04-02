#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import time
import config
import logging
from PIL import Image, ImageChops
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of
from globaldata import screen_queue
from globaldata import ip_found
from contextlib import contextmanager

logging.basicConfig(level=config.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(name="Screenshot")

# функция для обрезки монотонных областей
# сейчас не используется
def trim(im):
    pixel = (255, 255, 255)  # ориентируемся на белый цвет
    # pixel = im.getpixel((0,0))  # ориентируемся на пиксель с левого верхнего края
    bg = Image.new(im.mode, im.size, pixel)
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    logger.info(bbox)
    if bbox:
        return im.crop(bbox)
    else:
        return im


def get_screenshot(ip, port):
    thumfile = os.path.join(config.screen_folder, '{}_{}.png'.format(ip, port))
    url = 'http://{}:{}/'.format(ip, port)

    service_args = [
        '--proxy={}:{}'.format(config.tor_host, config.tor_port),
        '--proxy-type=socks5',
        ]

    driver = webdriver.PhantomJS(config.phantomjs_path, service_args=service_args)
    driver.set_window_size(config.screen_width, config.screen_height)
    driver.set_page_load_timeout(config.screen_wait)
    driver.set_script_timeout(config.screen_script_wait)

    driver.get(url)
    time.sleep(config.screen_pause)
    driver.execute_script("window.scrollTo(0, 0);")
    driver.save_screenshot(thumfile)
    driver.quit()

    img = Image.open(thumfile)
    img = img.crop((0, 0, config.screen_width, config.screen_height))
    # img = trim(img)
    img.save(thumfile)

    logger.info("Saved screen of {}:{}".format(ip, port))


def screener():
    try:
        while True:
            while screen_queue.qsize() == 0:
                time.sleep(1)

            ip, port, data = screen_queue.get()
            try:
                logger.info("Take {}:{} from screen queue".format(ip, port))
                get_screenshot(ip, port)

            except Exception as e:
                logger.error("Screen worker error: {}".format(e))

            finally:
                screen_queue.task_done() 

                # помещаем результат в очередь на отправку вне зависимости от наличия скриншота
                logger.info("Put {}:{} to result queue".format(ip, port))
                ip_found.put((ip, port, data))

    except Exception as e:
        logger.error("Screen thread error: {}".format(e))
        return
