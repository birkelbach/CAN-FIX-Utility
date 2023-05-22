#!/usr/bin/env python3

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

# This module is used to save and load complete configurations to give nodes


from PyQt5.QtCore import *
import logging
import json
import time
import threading
from collections import OrderedDict
import canfix
from . import devices
from . import connection
from . import config

log = logging.getLogger(__name__)

known_types = ["CHAR","BYTE","WORD","SHORT","USHORT","INT","UINT","DINT","UDINT","FLOAT"]
int_types = known_types[3:9]

canbus = connection.canbus

def setNodeConfiguration(sendNode, destNode, key, datatype, multiplier, value):
    ncq = canfix.NodeConfigurationSet(key = key)
    ncq.datatype = datatype
    ncq.multiplier = multiplier
    ncq.sendNode = sendNode
    ncq.destNode = destNode
    ncq.value = value

    conn = canbus.get_connection()
    conn.send(ncq.msg)
    endtime = time.time() + 1.0
    while(True):
        try:
            rmsg = conn.recv(timeout = 1.0)
        except connection.Timeout:
            canbus.free_connection(conn)
            return None
        p = canfix.parseMessage(rmsg)
        if isinstance(p, canfix.NodeConfigurationSet) and p.destNode == sendNode:
            canbus.free_connection(conn)
            return p
        else:
            if time.time() > endtime:
                canbus.free_connection(conn)
                return None

def queryNodeConfiguration(sendNode, destNode, key):
    ncq = canfix.NodeConfigurationQuery(key = key)
    conn = canbus.get_connection()
    ncq.sendNode = sendNode
    ncq.destNode = destNode
    conn.send(ncq.msg)
    endtime = time.time() + 1.0
    while(True):
        try:
            rmsg = conn.recv(timeout = 1.0)
        except connection.Timeout:
            canbus.free_connection(conn)
            return None
        p = canfix.parseMessage(rmsg)
        if isinstance(p, canfix.NodeConfigurationQuery) and p.destNode == sendNode:
            canbus.free_connection(conn)
            return p
        else:
            if time.time() > endtime:
                canbus.free_connection(conn)
                return None

# convienience function to get the node information from a node on the
# network.  Returns a tuple as (device type, model number, firmware version)
# if found otherwise it returns None
def getNodeInformation(sendNode, destNode):
    msg = canfix.NodeIdentification()
    conn = canbus.get_connection()
    msg.sendNode = sendNode
    msg.destNode = destNode
    conn.send(msg.msg)
    endtime = time.time() + 1.0
    while(True):
        try:
            rmsg = conn.recv(timeout = 1.0)
        except connection.Timeout:
            canbus.free_connection(conn)
            return None
        p = canfix.parseMessage(rmsg)
        if isinstance(p, canfix.NodeIdentification) and p.destNode == sendNode:
            canbus.free_connection(conn)
            return (p.device, p.model, p.fwrev)
        else:
            if time.time() > endtime:
                canbus.free_connection(conn)
                return None

class SaveThread(threading.Thread):
    def __init__(self, node, file):
        super(SaveThread, self).__init__()
        self.daemon = True
        self.getout = False
        self.attempts = 3
        self.timeout = 1.0
        self.nodeid = node
        self.statusCallback = lambda message : print(message)
        self.percentCallback = lambda *args: None
        self.finishedCallback = lambda *args: None
        self.conn = canbus.get_connection()
        self.output = {}
        self.file = file

    def run(self):
        log.debug("looking for node at {}".format(self.nodeid))
        result = getNodeInformation(config.node, self.nodeid)
        if result is not None:
            self.device = result[0]
            self.model = result[1]
            self.version = result[2]
            # Find the EDS file information for this node
            self.eds_info = devices.findDevice(self.device, self.model, self.version)
            if self.eds_info is not None:
                self.output['name'] = self.eds_info.name
            self.output['device'] = self.device
            self.output['model'] = self.model
            self.output['version'] = self.version
            self.output['cfgVersion'] = 1.0
            self.output['saved'] = time.ctime()
        else:
            log.error("Node Not Found")
            self.statusCallback(f"Node Not Found")
            return


        items = {}
        for x, each in enumerate(self.eds_info.configuration):
            result = queryNodeConfiguration(config.node, self.nodeid, each['key'])
            if 'depends' in each: # This is a dependent key
                key = each['depends']['key']
                for de in each['depends']['definitions']:
                    if isinstance(de['compare'], list):
                        if items[key]['value'] in de['compare']:
                            definition = de
                    else:
                        if items[key]['value'] == de['compare']:
                            definition = de
                if definition is not None:
                    result.datatype = definition['type']
                    name = definition['name']
            else:
                name = each['name']
                result.datatype = each['type']
            if 'multiplier' in each:
                mult = each['multiplier']
            else:
                mult = 1.0
            items[each["key"]] = {'name':name,'type':result.datatype,'multiplier':mult,'value':result.value}

            self.statusCallback(f"Saving - {each['key']} - {name}")
            self.percentCallback(int(x/len(self.eds_info.configuration)*100))
        self.output['items'] = items
        self.percentCallback(100)
        self.statusCallback("Finished")
        self.finishedCallback(True)
        canbus.free_connection(self.conn)
        json.dump(self.output, self.file, indent=2)

    def stop(self):
        self.getout = True
        self.join(2.0)
        if self.isAlive():
            log.warning("Config Save thread failed to stop properly")


class LoadThread(threading.Thread):
    def __init__(self, node, file):
        super(LoadThread, self).__init__()
        self.daemon = True
        self.getout = False
        self.attempts = 3
        self.timeout = 1.0
        self.nodeid = node
        self.statusCallback = lambda message : print(message)
        self.percentCallback = lambda *args: None
        self.finishedCallback = lambda *args: None
        self.conn = canbus.get_connection()
        self.input = json.load(file)
        if 'cfgVersion' in self.input:
            self.version = self.input['cfgVersion']
        else:
            self.version = None

    def run(self):
        if self.version is None or self.version != 1.0:
            log.error("Unknown configuration file")
            self.statusCallback("Unknown configuration file")
            return

        log.debug("looking for node at {}".format(self.nodeid))
        result = getNodeInformation(config.node, self.nodeid)
        if result is not None:
            self.device = result[0]
            self.model = result[1]
            self.version = result[2]
            # Find the EDS file information for this node
            self.eds_info = devices.findDevice(self.device, self.model, self.version)
            if self.eds_info is not None:
                if self.eds_info.deviceType != self.input['device']:
                    self.statusCallback("Device ID mismatch")
                    return
                if self.eds_info.modelNumber != self.input['model']:
                    self.statusCallback("Model Number mismatch")
                    return
                if self.eds_info.version != self.input['version']:
                    self.statusCallback("Version Number mismatch")
                    return
        else:
            log.error("Node Not Found")
            self.statusCallback(f"Node Not Found")
            return

        for x, key in enumerate(self.input['items']):
            item = self.input['items'][key]
            self.statusCallback(f"Sending Key {key}")
            result = setNodeConfiguration(config.node, self.nodeid, int(key), item['type'], item['multiplier'], item['value'])
            if result is None:
                self.statusCallback("Error writing Configuration key {key}")
            self.percentCallback(int(x/len(self.input['items'])*100))
        self.percentCallback(100)
        self.statusCallback("Finished")
        self.finishedCallback(True)
        canbus.free_connection(self.conn)


    def stop(self):
        self.getout = True
        self.join(2.0)
        if self.isAlive():
            log.warning("Config Load thread failed to stop properly")

