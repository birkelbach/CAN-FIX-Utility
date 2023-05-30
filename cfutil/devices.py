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
import urllib.request
import shutil
import hashlib
from collections import OrderedDict
import cfutil.config as config

log = logging.getLogger(__name__)

class Device:
    """Represents a single CAN-FIX device type"""
    def __init__(self, name, dtype, model, version):
        self.name = name
        self.deviceType = dtype
        self.modelNumber = model
        self.version = version
        self.fwUpdateCode = None
        self.fwDriver = None
        self.parameters = []
        self.configuration = []

    def __str__(self):
        return "{} type=0x{:02X}, model={:06X}, version={}".format(self.name, self.deviceType, self.modelNumber, self.version)

# The key to the devices dictionary is a tuple made up of
# the device id, model number and version
devices = {}

dirlist = os.listdir(config.datapath + "/eds")
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

# Downloads a file from the URI given and stores it in the filename given.  The filename
# should be a complete path to the file.
def download_file(uri, filename):
    with urllib.request.urlopen(uri) as response, open(filename, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


# Here we decide if it's time to download and check a new data file index.  Then we loop through
# the EDS file list and compare the SHA256 hashes against the files that we already have in the
# data directory.  If any of thme need to be downloaded then we do that now.
# TODO: Limit this to daily / weekly, etc.
if True:
    log.info(f"Retrieving Data Index from {config.data_index_uri}")

    with urllib.request.urlopen(config.data_index_uri) as response, open(config.datapath + "/cfdataindex.json", 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    # Open and load the index file
    with open(config.datapath + "/cfdataindex.json", 'r') as file:
        index = json.load(file)

    # Check the SHA256 Hash against the existing files
    for eds in index['eds_index']:
        if eds['filename'] in dirlist:
            with open(f"{config.datapath}/eds/{eds['filename']}") as json_file:
                sha = hashlib.sha256()
                while True:
                    data = json_file.read(65536)
                    if not data:
                        break
                    sha.update(data.encode())
                # If the SHA hash doesn't match the index then we need to download the file
                if sha.hexdigest() != eds['sha256']:
                    log.info(f"Updating EDS file {config.datapath}/eds/{eds['filename']}")
                    download_file(eds['uri'], f"{config.datapath}/eds/{eds['filename']}")
        else:
            log.info(f"Downloading EDS file {config.datapath}/eds/{eds['filename']}")
            download_file(eds['uri'], f"{config.datapath}/eds/{eds['filename']}")


dirlist = os.listdir(config.datapath + "/eds")
for filename in dirlist:
    if filename[-5:] == ".json":
        with open(config.datapath + "/eds/" + filename) as json_file:
            log.debug(f"Loading device file {filename}")
            d = json.load(json_file, object_pairs_hook=OrderedDict)
        try: # These are required
            name = d["name"]
            if isinstance(d["type"], str):
                dtype = int(d["type"], 0)
            if isinstance(d["model"], str):
                model = int(d["model"], 0)
            if isinstance(d["version"], str):
                version = int(d["version"], 0)
        except KeyError as e:
            log.warn(f"Problem with device file {filename}:{e}")
        newdevice = Device(name, dtype, model, version)
        newdevice.fwUpdateCode = int(d.get("firmware_code"),0)
        newdevice.fwDriver = d.get("firmware_driver")
        newdevice.parameters = getParameterList(d.get("parameters", []))
        # TODO: Sanitize configuration list
        newdevice.configuration = d.get("configuration", [])

        devices[(dtype, model, version)] = newdevice
        log.info(str(newdevice))

def findDevice(device, model, version):
    return devices.get((device, model, version), None)

# TODO: Write a function to verify the configuration and other parts of the file.
#          and some unit tests to test it all