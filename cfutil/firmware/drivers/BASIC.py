#!/usr/bin/python3

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

import math
import os
import logging
from .. import FirmwareBase
from .. import FirmwareError
from .. import StandardFileLoader

log = logging.getLogger(__name__)


class Driver(FirmwareBase):
    def __init__(self, filename, node, vcode, conn):
        FirmwareBase.__init__(self, filename, node, vcode, conn)
        self.file = StandardFileLoader(filename)
        # Here we check that the firmware verification code in the index.json file matches
        # what we are being asked to use.  If the code is present in the index.json file
        # and it's properly formed then we'll do the check otherwise we'll ignore it
        if 'vcode' in self.file.index:
            vc = self.file.index['vcode']
            if isinstance(vc, str):
                try:
                    if vc[0:2] == "0x":
                        vc = int(vc, 16)
                    else:
                        vc = int(vc)
                    if vc != vcode:
                        raise FirmwareError(f"Verification Code in {os.path.basename(filename)} does not match {vcode}")
                except ValueError:
                    log.warn(f"Verification code in {filename} is not properly formed")

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

    def __send_terminate(self, end_block = True):
        if end_block:
            data = []
            self.can.channel_send(self.channel, data)
            self.can.channel_recv(self.channel)
        data = [0xFE]
        self.can.channel_send(self.channel, data)
        self.can.channel_recv(self.channel)


    # Sends a single block of data from the file given by 'block'
    def __send_block(self, file, block):
        offset = file.offset + (block * file.blocksize)
        # This converts the block size into the proper value for sending in the message
        # see the protocol specification for details.
        mblocksize = math.log2(file.blocksize)
        if mblocksize % 1 != 0.0:
            raise FirmwareError(f"{file.blocksize} is an invalid block size")
        data = [file.blocktype, file.subsystem, int(mblocksize), offset & 0xFF, (offset & 0xFF00) >> 8, \
                            (offset & 0xFF0000) >> 16, (offset & 0xFF000000) >> 24]
        self.can.channel_send(self.channel, data)
        frame = self.can.channel_recv(self.channel)
        if frame.data[0] == 0xFF:
            if frame.data[1] == 0x00:
                raise FirmwareError(f"Bad Block Type Error: {file.blocktype}")
            elif frame.data[1] == 0x01:
                raise FirmwareError(f"Wrong Subsystem ID Error: {file.subsystem}")
            elif frame.data[1] == 0x02:
                raise FirmwareError(f"Unsupported Block Size Error: {file.blocksize}")
            elif frame.data[1] == 0x03:
                raise FirmwareError(f"Bad Address Error: {offset}")
            else:
                raise FirmwareError(f"Node Returned Error #{frame.data[1]} on Block Start")

        if offset + 8 > file.size: # last block of the file
            blockdata = file.data[offset:file.size]
        else:
            blockdata = file.data[offset:offset+file.blocksize]

        data = []
        for i, b in enumerate(blockdata):
            data.append(b)
            if i % 8 == 7:
                self.can.channel_send(self.channel, data)
                frame = self.can.channel_recv(self.channel)
                result = frame.data[0] + frame.data[1]*256 + frame.data[2]*65536 + frame.data[3]*16777216;
                # Check that the node is sending back the correct offset
                if result != i-7:
                    self.__send_terminate()
                    raise FirmwareError("Bad block offset received")
                self.__send_progress(8)
                data = []

        if data: # Send the leftovers if there is any data left
            self.can.channel_send(self.channel, data)
            frame = self.can.channel_recv(self.channel)
            result = frame.data[0] + frame.data[1]*256 + frame.data[2]*65536 + frame.data[3]*16777216;
            # Check that the node is sending back the correct offset
            if result != i-len(data)+1:
                self.__send_terminate()
                raise FirmwareError("Bad block offset received")

            self.__send_progress(len(data))

        # Send the end of block frame which is just an empty frame dlc=0
        self.can.channel_send(self.channel, [])
        self.can.channel_recv(self.channel)

    def __send_progress(self, bytes):
        self.bytes_sent += bytes
        self.sendProgress(float(self.bytes_sent / self.file.totalsize))


    def download(self):
        self.bytes_sent = 0
        # Calling this function requests the download from the node
        # and sets up the channel that we'll use.
        FirmwareBase.start_download(self)

        # Calculation the total number of blocks that we have to send
        # so that we can upate the progress appropriatly.  This would
        # be more accurate if we calculated it based on bytes of frames
        # but this will do for now.
        total_blocks = 0
        blocks_sent = 0

        for file in self.file.files:
            total_blocks += file.blockcount

        # Loop through the files and send them
        for file in self.file.files:
            for block in range(file.blockcount):
                self.sendStatus(f"Writing {file.filename}: Block {block+1} of {file.blockcount}")
                self.__send_block(file, block)
                blocks_sent += 1

        # Send end of transmission message
        data=[0xFD]
        self.can.channel_send(self.channel, data)
        frame = self.can.channel_recv(self.channel)

        self.sendStatus("Download Complete")
        self.sendProgress(1.0)
