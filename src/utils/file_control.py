#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
from collections import OrderedDict


def load_value(namespace, name, default=None):
    filename = 'data/{}.json'.format(namespace)

    try:
        with open(filename) as data_file:
            objects = json.load(data_file, object_pairs_hook=OrderedDict)

        if str(name) in objects.keys():
            return objects[str(name)]
    except FileNotFoundError:
        pass

    save_value(namespace, name, default)
    return default


def save_value(namespace, name, data):
    filename = 'data/{}.json'.format(namespace)
    objects = {}

    try:
        with open(filename) as data_file:
            objects = json.load(data_file, object_pairs_hook=OrderedDict)
    except FileNotFoundError:
        pass
    except json.decoder.JSONDecodeError:
        pass

    objects[str(name)] = data

    with open(filename, 'w') as data_file:
        json.dump(objects, data_file, indent=2)
