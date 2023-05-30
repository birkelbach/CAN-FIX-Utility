#!/usr/bin/python3

#  CAN-FIX Utilities - An Open Source CAN FIX Utility Package
#  Copyright (c) 2023 Phil Birkelbach
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


import os
import json
import logging
from . import config

log = logging.getLogger(__name__)

__data = {"version":1}

#datapath = appdirs.user_data_dir() + "/cfutil/"
datapath = config.datapath

log.info("Loading Settings")

def save_file():
    with open(datapath + "/settings.json", "w") as file:
        json.dump(__data, file, indent=2)

def run():
    global __data
    # See if the directory exists and if not create it
    os.makedirs(datapath + "/eds", exist_ok=True)


    try:
        with open(datapath + "/settings.json", "r") as file:
            __data = json.load(file)
    except FileNotFoundError:
        log.info("Creating New Settings File")
        save_file()

def get(key):
    return __data.get(key, None)

def set(key, v, save=True):
    __data[key] = v
    if save:
        save_file()

run()