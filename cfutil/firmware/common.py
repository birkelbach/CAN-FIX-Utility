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

import time
import logging
import canfix
import collections
from cfutil import connection

log = logging.getLogger(__name__)
canbus = connection.canbus

class FirmwareError(Exception):
    pass

class FirmwareBase:
    """Base Class for all firmware download drivers"""
    def __init__(self, filename, node, vcode, conn):
        self.filename = filename
        self.destNode = node
        self.firmwareCode = vcode
        self.can = conn

        # kill when set to True should stop downloads
        self.kill = False

        # This is our node number
        self.srcNode = 0xFF #0xFF is the default for configuration software
        self.__statusCallback = None
        self.__progressCallback = None
        self.__stopCallback = None

    def setProgressCallback(self, progress):
        if isinstance(progress, collections.abc.Callable):
            self.__progressCallback = progress
        else:
            raise TypeError("Argument passed is not a function")

    def setStatusCallback(self, status):
        if isinstance(status, collections.abc.Callable):
            self.__statusCallback = status
        else:
            raise TypeError("Argument passed is not a function")

    def setStopCallback(self, stop):
        if isinstance(stop, collections.abc.Callable):
            self.__stopCallback = stop
        else:
            raise TypeError("Argument passed is not a function")

    def sendStatus(self, status):
        """Function used by this object to test that the callback
            has been set and if so call it"""
        if self.__statusCallback:
            self.__statusCallback(status)

    def sendProgress(self, progress):
        """Function used by this object to test that the callback
           has been set and if so call it"""
        if self.__progressCallback:
            self.__progressCallback(progress)

    def stop(self):
        self.kill = True
        if self.__stopCallback:
            self.__stopCallback()

    # Download support functions
    def __getFreeChannel(self):
        """Waits for a half a second to see if there is any traffic on any
           of the channels and returns the channel number of the first
           free channel"""
        endtime = time.time() + 0.5
        channels = [0]*16
        while True: # Wait loop
            try:
                rframe = self.can.recv(0.1)
                if rframe is not None:
                    #print("***ch detect", rframe.error_state_indicator)
                    msg = canfix.parseMessage(rframe)
                    if isinstance(msg, canfix.TwoWayConnection):
                        self.channels[msg.channel] = 1
            except connection.Timeout:
                pass
            except Exception as e:
                print(e)
            finally:
                now = time.time()
                if now > endtime: break
        for ch, v in enumerate(channels):
            if v == 0: return ch
        return -1

    def __tryFirmwareReq(self):
        """Requests a firmware load, waits for 1/2 a second and determines
           if the response is correct and if so returns True returns
           False on timeout"""
        self.channel = self.__getFreeChannel()
        if self.channel < 0:
            raise FirmwareError("No Free Channel")
        #print("Channel found:", self.channel)
        print("self.firmwareCode = {}".format(self.firmwareCode))
        msg = canfix.UpdateFirmware(node=self.destNode, verification=self.firmwareCode, channel=self.channel)
        msg.sendNode = self.srcNode
        msg.msgType = canfix.MSG_REQUEST
        self.can.send(msg.msg)
        endtime = time.time() + 0.1
        while True: # Wait loop
            if self.kill:
                raise FirmwareError("Canceled")
            try:
                rframe = self.can.recv(0.1)
            except connection.Timeout:
                rframe = None

            if rframe != None:
                msg = canfix.parseMessage(rframe, silent=True)
                #print("****", rframe, rframe.is_error_frame)
                if isinstance(msg, canfix.UpdateFirmware):
                    if msg.destNode == self.srcNode:
                        if msg.status == canfix.MSG_SUCCESS:
                            return True
                        else:
                            log.warn("Firmware Update received with error code {}".format(msg.errorCode))
                            raise FirmwareError("Error {} Received".format(msg.errorCode))

            now = time.time()
            if now > endtime: return False
        return True

    def start_download(self):
        """this function is called from the derived class object to find
           a free channel and send the firmware request messages."""
        attempt = 0
        while True: # Firmware load request loop
            if self.kill: raise FirmwareError("Canceled")
            self.sendStatus("Download Attempt " + str(attempt))
            attempt += 1
            if self.__tryFirmwareReq(): break
        # This should be definied in the child and be specific for each driver
        #self.download()
