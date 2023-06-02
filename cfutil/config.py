#!/usr/bin/python3

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

# This file is for user configuration information.  Some data is automatically
# generated but can be overridden by the user if necessary.

import glob
import os
import sys
import shutil
import platform
import configparser
import appdirs

# The DataPath is the location of our XML device definition and
# protocol definition files.  It is simply a string of the absolute
# path to the data directory.

datapath = None
data_index_uri = None
data_download_interval = None

interface = None
channel = None
bitrate = None
node = None
timeout = 5.0

# Location where we will be storing our configuration file.
def_config_path = appdirs.user_config_dir() + "/cfutil"
def_config_file = def_config_path + "/main.ini"

def initialize(args):
    global config
    global interface
    global channel
    global bitrate
    global node
    global datapath
    global data_index_uri
    global data_download_interval

    if not os.path.exists(def_config_path):
        os.makedirs(def_config_path)
    # If the config file is not in that directory then copy it from the distribution
    if not os.path.exists(def_config_file):
        if os.path.exists(sys.path[0] + "/cfutil/data/main.ini"):
            sp = sys.path[0] + "/cfutil/data/main.ini" # The path where our script is installed
        else:
            sp = os.path.dirname(__file__) + "/data/main.ini"
        shutil.copyfile(sp, def_config_file)

    config = configparser.RawConfigParser()
    config.read(def_config_file)

    # Configure Application related data
    datapath = config.get("app", "data_directory", fallback=appdirs.user_data_dir() + "/cfutil")
    data_index_uri = config.get("app", "data_index_uri", fallback=None)
    data_download_interval = float(config.get("app", "data_download_interval", fallback=0))
    # Configure CAN connection related data
    if args.interface:
        interface = args.interface
    else:
        interface = config.get("can", "interface")
    if args.channel:
        channel = args.channel
    else:
        channel = config.get("can", "channel")
    try:
        if args.bitrate:
            bitrate = args.bitrate
        else:
            bitrate = config.getint("can", "bitrate")
    except:
        bitrate = 125000

    node = config.getint("canfix", "node")
    #auto_connect = config.getboolean("can", "auto_connect")

def set_value(section, option, value):
    config.set(section, option, value)
    with open(def_config_file, 'w') as file:
        config.write(file)

# This is different that reading the other options in that it
# gives us what is in the configuration file.
def get_value(section, option):
    return config.get(section, option)


# The following is the configured communications (serial) ports
# These are the defaults for most systems.  Others can simply be
# added as strings to the portlist[] list.  These device names
# should be suitable for use in the pySerial serial.port() property
# This can list every possible port on the machine.  The canbus
# module will test each one to see if it really is a serial port.
portlist = []

system_name = platform.system()
if system_name == "Windows":
    # Scan for available ports.
    for i in range(256):
        available.append(i)
elif system_name == "Darwin":
    # Mac
    portlist.extend(glob.glob('/dev/tty*'))
    portlist.extend(glob.glob('/dev/cu*'))
else:
    # Assume Linux or something else
    portlist.extend(glob.glob('/dev/ttyACM*'))
    portlist.extend(glob.glob('/dev/ttyUSB*'))
    portlist.extend(glob.glob('/dev/ttyS*'))
# Example for manually adding device names.
#portlist.append('/dev/ttyXYZ123456789')
