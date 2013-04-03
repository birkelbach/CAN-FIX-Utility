#!/usr/bin/python

#  CAN-FIX Utilities - An Open Source CAN FIX Utility Package 
#  Copyright (c) 2013 Phil Birkelbach
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

from intelhex import IntelHex
import crc
import canbus
from fwBase import FirmwareBase
import time

class Driver(FirmwareBase):
    def __init__(self, filename):
        FirmwareBase.__init__(self)
        self.__ih = IntelHex()
        self.__ih.loadhex(filename)
        
        cs = crc.crc16()
        for each in range(self.__ih.minaddr(), self.__ih.maxaddr()+1):
            cs.addByte(self.__ih[each])
        self.__size = self.__ih.maxaddr()+1
        self.__checksum = cs.getResult()

    def download(self, node):
        progress = 0.0
        self.statusCallback("Starting Download to Node " + str(node))
        while True:
            if self.kill==True: return
            time.sleep(1)
            self.progressCallback(progress)
            progress = progress + 0.1
            if progress > 1: break
        self.statusCallback("Download Finished")