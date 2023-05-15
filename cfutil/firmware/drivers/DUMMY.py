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

# This is a fake firmware driver that is just used for testing

from .. import crc
from ..common import FirmwareBase
import time

class Driver(FirmwareBase):
    def __init__(self, filename, node, vcode, conn):
        FirmwareBase.__init__(self, filename, node, vcode, conn)

    def download(self):
        progress = 0.0
        self.sendStatus("Starting Download to Node " + str(self.destNode))
        while True:
            if self.kill==True:
                self.sendProgress(0.0)
                self.sendStatus("Download Stopped")
                return
            time.sleep(0.1)
            self.sendProgress(progress)
            progress = progress + 0.01
            if progress >= 1: break
        self.sendProgress(1.0)
        self.sendStatus("Download Successful")
