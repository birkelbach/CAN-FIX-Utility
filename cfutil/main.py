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
    #l=['socketcan', 'serial', 'kvaser', 'pcan', 'usb2can']
    parser.add_argument('--interface', choices=l, help='CANBus Connection Interface Name')
    parser.add_argument('--channel', help='CANBus Channel or Device file')
    parser.add_argument('--bitrate', default=125, type=int, help='CANBus Bitrate')
    parser.add_argument('--node', default=0xFF, type=auto_int, help='Node Number')
    #parser.add_argument('--ip-address', help='CANBus Network Adapter IP Address')
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
    parser.add_argument('--timeout', type=int, default=0, help='Number of seconds to wait for a node to show up')
    parser.add_argument('--config-file', type=argparse.FileType('r'),
                            help='Alternate configuration file')
    parser.add_argument('--log-config', type=argparse.FileType('w'),
                            help='Alternate logger configuration file')


    args = parser.parse_args()

    config_file = args.config_file if args.config_file else 'cfutil/config/main.ini'
    log_config_file = args.log_config if args.log_config else config_file

    config.initialize(config_file, args)

    # Initialize Logger
    logging.config.fileConfig(log_config_file)
    log = logging.getLogger(__name__)

    # Now we start doing our job
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
