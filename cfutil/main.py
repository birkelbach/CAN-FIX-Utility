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

import argparse
import appdirs
import os
import sys
import shutil
import logging
import can
import logging.config
import cfutil.config as config

# Check for integers that could include hex values
def auto_int(x):
    return int(x, 0)

def main():
    parser = argparse.ArgumentParser(description='CAN-FIX Configuration Utility Program')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    l = sorted(can.interfaces.VALID_INTERFACES)
    parser.add_argument('--interface', choices=l, help='CANBus Connection Interface Name')
    parser.add_argument('--channel', help='CANBus Channel or Device file')
    parser.add_argument('--bitrate', default=125, type=int, help='CANBus Bitrate')
    parser.add_argument('--node', default=0xFF, type=auto_int, help='Our Node Number')
    parser.add_argument('--firmware-file', help='Firmware Filename')
    parser.add_argument('--firmware-code', type=auto_int, help='Firmware Verification Code')
    parser.add_argument('--firmware-driver', help='Firmware Driver to Use')
    parser.add_argument('--target-node', type=auto_int, help='Destination Node Number')

#    parser.add_argument('--device', help='CANFIX Device Name')
    parser.add_argument('--device-type', type=auto_int, help='CANFIX Target Device Type')
    parser.add_argument('--device-model', type=auto_int, help='CANFIX Target Device Model')
    parser.add_argument('--device-version', type=auto_int, help='CANFIX Target Device Model')
    parser.add_argument('--list-devices', action='store_true', help='List all known devices and their device IDs')
    parser.add_argument('--listen', action='store_true', help='Listen on the CANBus network and print to STDOUT')
    parser.add_argument('--frame-count', type=int, default=0, help='Number of frames to print before exiting')
    parser.add_argument('--raw', action='store_true', help='Display raw frames')
    parser.add_argument('--timeout', type=float, default=0, help='CAN-FiX Response Timeout')
    parser.add_argument('--node-timeout', type=int, default=0, help='Nodes will be considered dead if no message within this time')
    parser.add_argument('--load-configuration', type=argparse.FileType('r'),
                            help='Load the configuration from the file to --node')
    parser.add_argument('--save-configuration', type=argparse.FileType('w'),
                            help='Save the configuration to the file from --node')
    parser.add_argument('--config-file', type=argparse.FileType('r'),
                            help='Alternate configuration file')
    parser.add_argument('--log-config', type=argparse.FileType('w'),
                            help='Alternate logger configuration file')


    args = parser.parse_args()


    config.initialize(args)

    # Initialize Logger
    logging.config.fileConfig(config.log_config_file)
    log = logging.getLogger(__name__)

    # These need to be loaded after the logger is initialized
    from . import settings
    from . import mainCommand
    from . import connection

    try:
        connection.canbus.connect(config.interface, channel=config.channel)
    except:
        log.error("Failed to connect to {}".format(config.interface))
    result = mainCommand.run(args)
    # We don't run the GUI if mainCommand.run() executed some command or we
    # were in interactive mode.
    if args.interactive is False and not result:
        from . import mainTk
        app = mainTk.App(None)
        app.run()

    connection.canbus.stop()
    connection.canbus.join()

if __name__ == "__main__":
    main()
