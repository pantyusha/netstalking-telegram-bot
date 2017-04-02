#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import config
import random
import requests
import string

task_total_weight = 0
task_struct = {}


def random_string(len):
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(len))


def load():
    global task_struct
    task_struct = json.load(open(config.task_file, 'r'))
    chances_create()
    random.seed()


def chances_create():
    sum = 0
    global task_struct, task_total_weight
    for task in task_struct:
        weight = int(task_struct[task]["weight"])
        task_struct[task]["chance"] = weight + sum
        sum += weight
    task_total_weight = sum


def get_task():
    global task_total_weight
    task_chance = random.randint(0, task_total_weight)
    task = {}
    task_name = ""
    if config.DEBUG:
        print("Task chance: {}".format(task_chance))

    for task_name in task_struct:
        if task_chance <= task_struct[task_name]["chance"]:
            task = task_struct[task_name]
            break

    if task == {}:
        return "wtf with task?"

    hashtags = ' '.join(["#{}".format(hashtag) for hashtag in task["hashtags"]])

    if task_name == "keyword_ip_search":
        keyword = random.choice(task["keywords"])
        links_str = '\n'.join([link.format(keyword) for link in task["links"]])

        return "{0}\nПоищи IP по запросу {1}\n{2}".format(hashtags, keyword, links_str)

    elif task_name == "random_symbols_search":
        length = random.randint(task["min_length"], task["max_length"])
        rand_string = random_string(length)      
        links_str = '\n'.join([link.format(rand_string) for link in task["links"]])

        return "{0}\nПоищи страницы по запросу {1}\n{2}".format(hashtags, rand_string, links_str)

    elif task_name == "random_onion":
        response = requests.get(task["url"], timeout=config.http_wait, proxies=config.tor_proxy, allow_redirects=False)
        location = response.headers['Location']

        return "{0}\nОткрой onion-сайт:\n{1}".format(hashtags, location.replace(".onion", ".onion.cab"))

    elif task_name == "random_darknet":
        darknet = random.choice(task["darknets"])
        links_str = '\n'.join(link for link in darknet["links"])
        darknet_hashtags = ' '.join(["#{}".format(hashtag) for hashtag in darknet["hashtags"]])

        return "{} {}\nА повкуривай-ка {}!\n{}".format(hashtags, darknet_hashtags, darknet["name"], links_str)
