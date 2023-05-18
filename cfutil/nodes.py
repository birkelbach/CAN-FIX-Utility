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

from threading import Thread
import time
import logging
import can
import canfix
from . import connection
from . import config
from . import devices

log = logging.getLogger(__name__)

class Paramter():
    def __init__(self):
        self.nodeid = None
        self.pid = None
        self.index = None
        self.indexName = None
        self.name = None
        self.type = ''
        self.value = None
        self.units = ''
        self.quality = ''
        #TODO add min / max and meta information

    # This function returns True if a change was made
    def update(self, msg):
        # TODO Check that we make a change
        self.lastupdate = time.time()
        self.nodeid = msg.node
        self.pid = msg.identifier
        self.index = msg.index
        self.indexName = msg.indexName
        self.name = msg.name
        self.type = msg.type
        if msg.indexName is not None:
            self.name += " {} #{}".format(msg.indexName, msg.index+1)
        # Save some time by only doing this if we've changed
        if self.value != msg.value:
            self.valstring = msg.valueStr(units = True)
            self.value = msg.value
            self.units = msg.units
        #TODO deal with quality string
        #TODO add min / max and meta information
        self.lastupdate = time.time()
        return True


class Node():
    def __init__(self, nodeid):
        self.nodeid = nodeid
        self.__deviceid = None
        self.__version = None
        self.__model = None
        self.name = "Unknown Device"
        self.__device = None
        self.__description = bytearray([0]*256)
        self.status = 0
        self.laststatus = None
        self.lastupdate = time.time()
        self.userdata = {}

    # this function is meant to receive the packet number and four character bytes
    # of a node description message.
    def set_description(self, packet_num, bytes):
        # TODO Deal with growing the thing if necessary.
        index = packet_num*4
        self.__description[index:index+4] = bytes

    @property
    def deviceid(self):
        return self.__deviceid

    @deviceid.setter
    def deviceid(self, v):
        self.__deviceid = v
        if self.__deviceid != None and self.__model != None and self.__version != None:
            self.device = devices.findDevice(self.__deviceid, self.__model, self.__version)
        self.lastupdate = time.time()

    @property
    def version(self):
        return self.__version

    @version.setter
    def version(self, v):
        self.__version = v
        if self.__deviceid != None and self.__model != None and self.__version != None:
            self.device = devices.findDevice(self.__deviceid, self.__model, self.__version)
        self.lastupdate = time.time()

    @property
    def model(self):
        if self.__model is not None:
            return hex(self.__model).lstrip('0x').upper()
        else:
            return None

    @model.setter
    def model(self, v):
        self.__model = v
        if self.__deviceid != None and self.__model != None and self.__version != None:
            self.device = devices.findDevice(self.__deviceid, self.__model, self.__version)
        self.lastupdate = time.time()

    def update(self):
        self.lastupdate = time.time()

    @property
    def device(self):
        return self.__device

    @device.setter
    def device(self, d):
        if d is not None:
            self.name = d.name
            self.__device = d

    @property
    def description(self):
        return self.__description.decode('ascii')

    @property
    def status_str(self):
        if self.status == 0:
            return "OK"
        else:
            return f"Error {self.status}"


class NodeThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.getout = False
        # list of nodes.  The node id = the index
        self.nodelist = [None]*256
        # dictionary to contain all of the received parameters.  The key is the parameter id
        self.parameterlist = {}
        self.__add_node_callback = None
        self.__del_node_callback = None
        self.__update_node_callback = None
        self.__add_parameter_callback = None
        self.__del_parameter_callback = None
        self.__update_parameter_callback = None


    def __add_node(self, nodeid, sendid=True):
        self.nodelist[nodeid] = Node(nodeid)
        if sendid:
            # Send a node identification request for the new node
            nid = canfix.NodeIdentification()
            nid.sendNode = config.node
            nid.destNode = nodeid
            self.conn.send(nid.msg)
        if self.__add_node_callback is not None:
            self.__add_node_callback(self.nodelist[nodeid])


    def set_node_callbacks(self, add, delete, update):
        self.__add_node_callback = add
        self.__del_node_callback = delete
        self.__update_node_callback = update

    def set_parameter_callbacks(self, add, delete, update):
        self.__add_parameter_callback = add
        self.__del_parameter_callback = delete
        self.__update_parameter_callback = update


    # This takes the message and deals with it.  It handles creating nodes and parameters
    # if needed as well as updating
    def update_node(self, msg):
        if isinstance(msg, canfix.NodeIdentification):
            if msg.msgType == canfix.MSG_RESPONSE:
                if self.nodelist[msg.sendNode] == None:
                    self.__add_node(msg.sendNode, sendid = False)
                else:
                    if self.__update_node_callback is not None:
                        self.__update_node_callback(self.nodelist[msg.sendNode])
                x = self.nodelist[msg.sendNode]
                x.deviceid = msg.device
                x.version = msg.fwrev
                x.model = msg.model
        elif isinstance(msg, canfix.NodeDescription):
            if self.nodelist[msg.sendNode] == None:
                self.__add_node(msg.sendNode, sendid = False)
            self.nodelist[msg.sendNode].set_description(msg.packetnumber, msg.chars)
        elif isinstance(msg, canfix.NodeStatus):
            if self.nodelist[msg.sendNode] == None:
                self.__add_node(msg.sendNode)
            else:
                self.nodelist[msg.sendNode].update()
                if self.__update_node_callback is not None:
                        self.__update_node_callback(self.nodelist[msg.sendNode])
            if msg.controlCode == 0: # Status
                self.nodelist[msg.sendNode].status = msg.value
        elif isinstance(msg, canfix.Parameter):
            # If we don't already have this parameter then add it
            pid = (msg.identifier, msg.index)
            if pid not in self.parameterlist:
                self.parameterlist[pid] = Paramter()
                if self.__add_parameter_callback:
                    self.__add_parameter_callback(self.parameterlist[pid])
            # either way update the parameter in the dict and if the callback is
            # assigned then call it
            if self.parameterlist[pid].update(msg) and self.__update_parameter_callback:
                    self.__update_parameter_callback(self.parameterlist[pid])
            # If we don't have then node in the list yet then add it
            if self.nodelist[msg.node] == None:
                self.__add_node(msg.node)
            # If it's already there then we can update the time
            else:
                self.nodelist[msg.node].update()

    # This loops through everything and makes sure we're all goo
    # it'll delete nodes and paramters if they have not been updated
    # in time
    def checkall(self):
        now = time.time()
        for i, v in enumerate(self.nodelist):
            if v is not None:
                if now > v.lastupdate + 5.0: # If node is more than 4 seconds old
                    self.nodelist[i] = None  # Delete it
                    if self.__del_node_callback is not None:
                        self.__del_node_callback(v)
        # To delete old parameters we have to add the ones we want to get
        # rid of a list and then delete the items after we finish iterating
        # through the loop.
        del_list = []
        for k in self.parameterlist:
            if now > self.parameterlist[k].lastupdate + 5:
                if self.__del_parameter_callback is not None:
                    self.__del_parameter_callback(self.parameterlist[k])
                del_list.append(k)

        for each in del_list:
            self.parameterlist.pop(each)


    def run(self):
        lastscan = time.time()
        self.conn = connection.canbus.get_connection()
        while(not self.getout):
            thisscan = time.time()
            try:
                msg = self.conn.recv(0.5)
                x = canfix.parseMessage(msg)
                self.update_node(x)
            except connection.Timeout:
                pass
            except Exception as e:
                log.error(e)
            if thisscan > lastscan + 2:
                self.checkall()
                lastscan = thisscan



    def stop(self):
        self.getout = True


