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
from . import crc
import time
import can
from . import FirmwareBase
from cfutil import connection


class Driver(FirmwareBase):
    def __init__(self, filename, node, vcode, conn):
        FirmwareBase.__init__(self, filename, node, vcode, conn)
        self.__ih = IntelHex()
        self.__ih.loadhex(filename)

        cs = crc.crc16()
        for each in range(self.__ih.minaddr(), self.__ih.maxaddr()+1):
            cs.addByte(self.__ih[each])
        self.__size = self.__ih.maxaddr()+1
        self.__checksum = cs.getResult()
        self.__progress = 0.0
        self.blocksize = 128
        self.__currentblock = 0

    def setArg(self, argname, value):
        if argname == "blocksize":
            self.blocksize = value

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

    def __waitBufferResponse(self, channel, offset):
        endtime = time.time() + 0.5
        while True:
            try:
                rframe = self.can.recv(0.5)
            except connection.Timeout:
                pass
            else:
                if rframe.arbitration_id == 0x7E0 + channel + 1:
                    if (rframe.data[0] + (rframe.data[1]<<8)) == offset:
                        break
                    else:
                        raise connection.BadOffset
            now = time.time()
            if now > endtime:
                raise connection.Timeout
        return True

    def __fillBuffer(self, ch, address, data):
        length = len(data)
        #print("Address 0x{:08X} {}".format(address, address))
        sframe = can.Message(arbitration_id = 0x7E0 + ch, is_extended_id =False,
                             data=[0x01, address & 0xFF, (address & 0xFF00) >> 8, (address & 0xFF0000) >> 16, (address & 0xFF000000) >> 24, 0, 1])
        self.can.send(sframe)
        endtime = time.time() + 0.5
        while True: # Channel wait loop
            try:
                rframe = self.can.recv(1)
            except connection.Timeout:
                pass
            else:
                if rframe.arbitration_id == sframe.arbitration_id+1 and \
                    rframe.data == sframe.data: break
            now = time.time()
            if now > endtime:
                raise connection.Timeout
        for n in range(length//8):
            # print("[{:02}: ".format(n), end='')
            # for each in data[(8*n):(8*n) + 8]:
            #     print("{:02X} ".format(each), end='')
            # print("]")
            sframe.data = data[(8*n):(8*n) + 8]
            sframe.dlc=8
            self.can.send(sframe)
            self.__waitBufferResponse(ch, (n+1)*8)
            #time.sleep(0.3)
            # TODO Need to deal with the abort from the uC somewhere
        return True

    def __erasePage(self, ch, address):
        sframe = can.Message(arbitration_id = 0x7E0 + ch, is_extended_id =False,
                             data=[0x02, address & 0xFF, (address & 0xFF00) >> 8, (address & 0xFF0000) >> 16, (address & 0xFF000000) >> 24])
        self.can.send(sframe)
        endtime = time.time() + 0.5
        while True: # Channel wait loop
            try:
                rframe = self.can.recv(0.1)
            except connection.Timeout:
                pass
            else:
                if rframe.arbitration_id == sframe.arbitration_id+1 and \
                    rframe.data == sframe.data: break
            now = time.time()
            if now > endtime:
                raise connection.Timeout
        return True

    def __writePage(self, ch, address):
        sframe = can.Message(arbitration_id = 0x7E0 + ch, is_extended_id =False,
                             data=[0x03, address & 0xFF, (address & 0xFF00) >> 8, (address & 0xFF0000) >> 16, (address & 0xFF000000) >> 24])
        self.can.send(sframe)
        endtime = time.time() + 0.5
        while True: # Channel wait loop
            try:
                rframe = self.can.recv(1)
            except connection.Timeout:
                pass
            else:
                if rframe.arbitration_id == sframe.arbitration_id+1 and \
                    rframe.data == sframe.data: break
            now = time.time()
            if now > endtime:
                raise connection.Timeout

    def __sendComplete(self, ch):
        sframe = can.Message(arbitration_id = 0x7E0 + ch, is_extended_id =False,
                             data=[0x05, self.__checksum & 0xFF, (self.__checksum & 0xFF00) >> 8, \
                                   self.__size & 0xFF, (self.__size & 0xFF00) >> 8, \
                                   (self.__size & 0xFF0000) >> 16, (self.__size & 0xFF000000) >> 24])
        self.can.send(sframe)
        endtime = time.time() + 0.5
        while True: # Channel wait loop
            try:
                rframe = self.can.recv(1)
            except connection.Timeout:
                pass
            else:
                if rframe.arbitration_id == sframe.arbitration_id+1 and \
                    rframe.data == sframe.data: break
            now = time.time()
            if now > endtime:
                raise connection.Timeout

    # TODO Need to make sure this fails properly when something goes wrong and
    #      it might be nice to have some retires on blocks that fail.  Might
    #      make this more robust.
    # TODO We are not sending partial frames.  This probably isn't a big deal
    #      but it's not exactly like the specification.  Maybe change the spec,
    #      that might simplify the bootloader
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
