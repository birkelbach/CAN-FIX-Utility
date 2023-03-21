#!/usr/bin/env python

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

# Module interprets the command line arguments and performs the job(s) given

import traceback
import logging
import can
import canfix
import cfutil.config as config
import cfutil.connection as connection
import cfutil.devices as devices

log = logging.getLogger(__name__)


def list_devices():
    print("Device List")
    print("-----------------------")
    for each in devices.devices:
        print(each)
        #print(each.name, '[' + hex(each.deviceType) + ']')

def listen(conn, msg_count, raw):
    log.debug("Listen with msg_count = {}, raw = {}".format(msg_count, raw))
    count = 0
    while True:
        try:
            msg = conn.recv(1.0)
            if msg:
                #print(str(msg) + canfix.parameters[msg.arbitration_id].name)
                if raw:
                    print(str(msg))
                else:
                    x = canfix.parseMessage(msg)
                    print(x)
                count+=1
                if msg_count != 0:
                    if count >= msg_count: break
        except KeyboardInterrupt:
            break
        except connection.Timeout:
            #TODO do some timeout checking here
            pass
        except Exception as e:
            if hasattr(e, 'message'):
                log.error(e.message)
            else:
                log.error(str(e))

# def findDevice(did):
#     for each in devices.devices:
#         if each.DeviceId == did:
#             return each
#     return None

def fwstatus(status):
    print(status)

def load_firmware(conn, filename, args):
    import cfutil.firmware as firmware
    driver = None
    vcode = None
    if args.firmware_driver:
        driver = args.firmware_driver
    if args.firmware_code:
        vcode = args.firmware_code
    if args.target_node:
        node = args.target_node
    else:
        print("ERROR: Target Node must be given")
        return

    if args.device_type or args.device_model or args.device_version:
        if not args.device_type:
            print("ERROR: Device type must be given")
        if not args.device_model:
            print("ERROR: Device model number must be given")
        if not args.device_version:
            print("ERROR: Device firmware version must be given")
        if args.device_type and args.device_model and args.device_version:
            device = devices.findDevice(args.device_type, args.device_model, args.device_version)
            if device:
                print("Found {}".format(device.name))
                print("Using Firmware Driver", device.fwDriver)
                driver = device.fwDriver
                vcode = device.fwUpdateCode
            else:
                print("ERROR: Unknown Device Given")
                return

    # If the device definition wasn't given on the command line then we'll
    # look on the network for it.
    if driver is None:
        # Send node Identification message to node
        m = can.Message(arbitration_id=0x6E0, is_extended_id=False, data=[0, node])
        conn.send(m)
        while True:
            try:
                frame = conn.recv(1.0)
                if frame.arbitration_id == 0x6E0 + node:
                    msg = canfix.parseMessage(frame)
                    if msg is canfix.NodeIdentification:
                        device = devices.findDevice(msg.device, msg.model, msg.fwrev)
                    if device:
                        print("Found", device.name, "At Node", node)
                        print("Using Firmware Driver", device.fwDriver)
                        driver = device.fwDriver
                        vcode = device.fwUpdateCode
                    else:
                        print("ERROR: Unknown Device at that node")
                        return
            except connection.Timeout:
                print("ERROR: No device found at node 0x{:02X}", )
                break
            except KeyboardInterrupt:
                return

    try:
        fw = firmware.Firmware(driver, filename, node, vcode, conn)
        fw.setStatusCallback(fwstatus)
        fw.srcNode = args.node
        fw.destNode = node
        fw.download()
    except KeyboardInterrupt:
        fw.kill = True


def run(args):
    cmdrun = False
    try:
        conn = connection.canbus.get_connection()
        if args.list_devices == True:
            list_devices()
            cmdrun = True
        if args.firmware_file:
            cmdrun = True
            if not connection.canbus.connected:
                raise(Exception("ERROR: No valid CAN Bus connection"))
            if args.target_node == None:
                # TODO: it might be nice if the argument parser did this for us?
                raise(Exception("ERROR: Target Node Number Requried"))

            load_firmware(conn, args.firmware_file, args)

        if args.listen == True:
            listen(conn, args.frame_count, args.raw)
            cmdrun = True
    except Exception as e:
        #print(e)
        traceback.print_exc()
        #raise(e)
    finally:
        connection.canbus.free_connection(conn)
        return cmdrun

if __name__ == "__main__":
    run(None)
