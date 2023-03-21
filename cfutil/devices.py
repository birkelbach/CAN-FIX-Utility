#!/usr/bin/env python

#  CAN-FIX Utilities - An Open Source CAN FIX Utility Package
#  Copyright (c) 2012 Phil Birkelbach
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

# This module exposes a list of all the devices that we know how to talk to.
# These devices are all defined by JSON files in config.DataPath/devices
# There is one JSON file per device.

import os
import logging
import json
from collections import OrderedDict
import cfutil.config as config

log = logging.getLogger(__name__)

class Device:
    """Represents a single CAN-FIX device type"""
    def __init__(self, name, dtype, model, version):
        self.name = name
        self.deviceType = int(dtype, 0)
        self.modelNumber = int(model, 0)
        self.version = int(version, 0)
        self.fwUpdateCode = None
        self.fwDriver = None
        self.parameters = []
        self.configuration = []

    def __str__(self):
        return "{} type=0x{:02X}, model={:06X}, version={}".format(self.name, self.deviceType, self.modelNumber, self.version)

devices = []

dirlist = os.listdir(config.DataPath + "devices")
log.debug("Loading Devices")


def getParameterList(pl):
    l = []
    for p in pl:
        if(type(p) == str):
            l.append(int(p, 0))
        else:
            l.append(int(p))
    l.sort()
    return l

for filename in dirlist:
    if filename[-5:] == ".json":
        with open(config.DataPath + "devices/" + filename) as json_file:
            log.debug("Loading device file {}".format(filename))
            d = json.load(json_file, object_pairs_hook=OrderedDict)
        try: # These are required
            name = d["name"]
            dtype = d["type"]
            model = d["model"]
            version = d["version"]
        except KeyError as e:
            log.warn("Problem with device file {}:{}".format(config.DataPath + "devices/" + filename, e))
        newdevice = Device(name, dtype, model, version)
        newdevice.fwUpdateCode = int(d.get("firmware_code"),0)
        newdevice.fwDriver = d.get("firmware_driver")
        newdevice.parameters = getParameterList(d.get("parameters", []))
        # TODO: Sanitize configuration list
        newdevice.configuration = d.get("configuration", [])

        devices.append(newdevice)
        log.info(str(newdevice))

def findDevice(device, model, version):
    for each in devices:
        if each.deviceType == device and each.modelNumber == model:
            return each
    return None
