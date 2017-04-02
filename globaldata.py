#!/usr/bin/python3
# -*- coding: utf-8 -*-
import config
import queue

# очередь для хранения окончательных результатов
ip_found = queue.Queue()
# очередь для хранения адресов, которые нужно заскриншотить
screen_queue = queue.Queue()
# список диапазонов, по которым нужно сканировать
ip_ranges = []
