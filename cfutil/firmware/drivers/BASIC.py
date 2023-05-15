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

from .. import crc
import time
import can
from .. import FirmwareBase
from .. import StandardFileLoader
from cfutil import connection


class Driver(FirmwareBase):
    def __init__(self, filename, node, vcode, conn):
        FirmwareBase.__init__(self, filename, node, vcode, conn)
        self.file = StandardFileLoader(filename)
        self.__progress = 0.0

    # These are overriding the base class indexing methods
    # This is so that we can use the Driver["blocksize"]
    # mechanism for accessing this argument
    def __getitem__(self, idx):
        if idx == "blocksize":
            return self.blocksize
        else:
            raise IndexError

    def __setitem__(self, idx, value):
        if idx == "blocksize":
            self.blocksize = value
        else:
            raise IndexError

    # .blocksize property
    def setBlocksize(self, value):
        self.__blocksize = value
        self.__blocks = self.__size // self.__blocksize
        if self.__size % self.__blocksize != 0:
            self.__blocks = self.__blocks+1
        #print("Block count = {}".format(self.__blocks))

    def getBlocksize(self):
        return self.__blocksize

    blocksize = property(getBlocksize, setBlocksize)


    def download(self):
        data=[]
        FirmwareBase.start_download(self)
        for n in range(self.__blocks * self.__blocksize):
            data.append(self.__ih[n])

        for block in range(self.__blocks):
            try:
                address = block * self.__blocksize
                self.sendStatus("Writing Block %d of %d" % (block+1, self.__blocks))
                self.sendProgress(float(block) / float(self.__blocks))
                self.__currentblock = block
                while(self.__fillBuffer(self.channel, address, data[address:address+self.blocksize])==False):
                    if self.kill:
                        self.sendProgress(0.0)
                        self.sendStatus("Download Stopped")
                        return
                        #raise firmware.FirmwareError("Canceled")

                # Erase Page
                #print( "Erase Page Address = {}".format(address))
                self.__erasePage(self.channel ,address)

                # Write Page
                #print("Write Page Address = {}".format(address))
                self.__writePage(self.channel ,address)
            except connection.Timeout:
                self.sendProgress(0.0)
                self.sendStatus("FAIL: Timeout Writing Data")
                return
            except connection.BadOffset:
                self.sendProgress(0.0)
                self.sendStatus("FAIL: Bad Block Offset Received")
                return

        #self.__progress = 1.0
        #print("Download Complete Checksum".format(hex(self.__checksum), "Size", self.__size))
        try:
            self.__sendComplete(self.channel)
            self.sendStatus("Download Complete Checksum 0x%X, Size %d" % (self.__checksum, self.__size))
            self.sendProgress(1.0)
        except connection.Timeout:
            self.sendProgress(0.0)
            self.sendStatus("FAIL: Timeout While Finalizing Download")

        #FirmwareBase.end_download()
