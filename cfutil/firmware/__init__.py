#!/usr/bin/python

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

import can
import string
import argparse

#from . import common as fw
from .common import *
from .stdfile import *

def Firmware(driver, filename, node, vcode, conn):
    if driver == "AT328":
        from .drivers import AVR8
        d = AVR8.Driver(filename, node, vcode, conn)
        d["blocksize"] = 128
        return d
    elif driver == "AT2561":
        from .drivers import AVR8
        d = AVR8.Driver(filename, node, vcode, conn)
        d["blocksize"] = 256
        return d
    elif driver == "BASIC":
        from .drivers import BASIC
        d = BASIC.Driver(filename, node, vcode, conn)
        return d
    elif driver == "DUMMY":
        from .drivers import DUMMY
        return DUMMY.Driver(filename, node, vcode, conn)
    else:
        raise FirmwareError("No such driver")

def GetDriverList():
    return {"AT328":"ATmega328",
            "AT2561":"Atmega2561",
            "BASIC":"Basic Standard Driver",
            "DUMMY":"Test Driver"}

# def config():
#     parser = argparse.ArgumentParser(description='CANFIX Firmware Downloader 1.0')
#     parser.add_argument('--filename', '-f', nargs=1, help='Intel Hex File to Download', required=True)
#     parser.add_argument('--port', '-p', nargs=1, help='Serial Port to find CANBus interface')
#     parser.add_argument('--node', '-n', type=int, nargs=1, help='CAN-FIX Node number of device')
#     args = parser.parse_args()
#     args = vars(args)
#     output = {}
#     if args['port'] != None:
#         output["portname"]= args['port'][0]
#     else:
#         output["portname"] = ""
#
#     output["filename"] = args['filename'][0]
#     output["node"] = args['node'][0]
#
#     return output
#
#
# #***** MAIN ROUTINE *****
# def main():
#     exit()
#
# if __name__ == '__main__':
#     main()
