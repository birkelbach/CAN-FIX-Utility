#!/usr/bin/env python3

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

# This module is used to save and load complete configurations to give nodes


from PyQt5.QtCore import *
import os
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
    def __init__(self):
        super(SaveThread, self).__init__()
        self.daemon = True
        self.getout = False
        self.attempts = 3
        self.timeout = 1.0
        self.nodeid = None
        self.statusCallback = lambda message, percent, done : print(message)
        self.percentCallback = lambda percent : print(percent)
        self.finishedCallback = lambda finished : print(finished)
        self.startKey = 0
        self.endKey = 0
        self.cfgList = []
        self.conn = canbus.get_connection()
        self.output = OrderedDict()

    # Takes an integer key and attempts to read the key from the node at
    # self.nodeid.  If successful it returns the data that was received.  On
    # timeout it returns None and on error returns and empty list.
    def getConfigItem(self, key):
        msg = canfix.NodeConfigurationQuery(key=key)
        msg.sendNode = config.node
        msg.destNode = self.nodeid
        for x in range(self.attempts): # How many times to try
            self.conn.send(msg.msg)  # Send request
            while(True):
                start = time.time()
                try:
                    result = self.conn.recv(timeout = self.timeout)
                except connection.Timeout:
                    break
                else:
                    p = canfix.parseMessage(result)
                    if isinstance(p, canfix.NodeConfigurationQuery) and p.destNode == config.node:
                        if p.error:
                            return []
                        return p.rawdata[1:]
                    else:
                        if time.time() - start > self.timeout:
                            break


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
        else:
            log.error("Node Not Found")

        self.output['items'] = []
        for x, each in enumerate(self.eds_info.configuration):
            result = self.getConfigItem(each['key'])
            d = OrderedDict([("key", each["key"]), ('name', each['name']), ('type',each['type'])])
            d['data'] = []
            for i in result:
                d['data'].append("0x{:02X}".format(i))
            self.output['items'].append(d)
            if self.getout == True:
                self.statusCallback("Canceled")
                self.finishedCallback(False)
                canbus.free_connection(self.conn)
                return
            self.statusCallback("Saving - {}".format(each['name']))
            self.percentCallback(int(x/len(self.eds_info.configuration)*100))

        self.percentCallback(100)
        self.statusCallback("Finished")
        self.finishedCallback(True)
        canbus.free_connection(self.conn)


    def stop(self):
        self.getout = True
        self.join(2.0)
        if self.isAlive():
            log.warning("Config Save thread failed to stop properly")


class ConfigSave(QObject):
    status = pyqtSignal(str)     # Gives a string message of the progress status
    percent = pyqtSignal(int)    # percent complete 0-100
    finished = pyqtSignal(bool)  # True if sucessful, False if falied or canceled

    def __init__(self, nodeid, file):
        super(ConfigSave, self).__init__()
        self.nodeid = nodeid
        self.file = file
        self.startKey = 0
        self.endKey = 0
        self.eds_info = None

    def __finished(self, result):
        if result:
            print(json.dumps(self.sthread.output, indent=2))
            json.dump(self.sthread.output, self.file, indent=2)
        self.finished.emit(result)

    def start(self):
        self.sthread = SaveThread()
        self.sthread.startKey = self.startKey
        self.sthread.endKey = self.endKey
        self.sthread.nodeid = self.nodeid
        self.sthread.statusCallback = self.status.emit
        self.sthread.percentCallback = self.percent.emit
        self.sthread.finishedCallback = self.__finished
        self.sthread.start()

    def stop(self):
        self.sthread.stop()


class ConfigLoad(QObject):
    pass
