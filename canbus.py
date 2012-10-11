#!/usr/bin/python

import serial
from serial.tools.list_ports import comports
import time

# This module is to abstract the interface between the code and the
# CANBus communication devices.  Right now it only works with the
# EasySync USB2-F-7xxx devcies.  The idea is to create classes for
# each type of device that we want to use and have a common interface
# for each.  While connecting we'd figure out what kind of device that
# we have and then set pointers to the right device classes so the rest
# of the program doesn't have to worry about what device it is using

class BusError(Exception):
    """Base class for exceptions in this module"""
    pass

class BusInitError(BusError):
    """CAN Bus Initialization Error"""
    def __init__(self, msg):
            self.msg = msg

class BusReadError(BusError):
    """CAN Bus Read Error"""
    def __init__(self, msg):
        self.msg = msg

class BusWriteError(BusError):
    """CAN Bus Write Error"""
    def __init__(self, msg):
        self.msg = msg

class DeviceTimeout(Exception):
    """Device Timeout Exception"""
    pass

class Device():
    """Base class for all the devices"""
    def __init__(self, bitrate=125):
        self.bitrate = bitrate

    def setport(self,ser):
        self.ser = ser


class EasyDevice(Device):
    """Class that represents an EasySync USB2-F-7x01 USB to CANBus device"""
    def _readResponse(self):
        str = ""

        while 1:
            x = self.ser.read()
            if len(x) == 0:
                raise DeviceTimeout
            else:
                str = str + x
                if x == "\r": # Good Response
                    return str
                if x == "\x07": # Bell is error
                    raise BusReadError("USB2-F-7x01 Returned Bell")

    def init(self):
        bitrates = {10:"S0\r", 20:"S1\r", 50:"S2\r", 100:"S3\r", 
                    125:"S4\r", 250:"S5\r", 500:"S6\r", 800:"S7\r", 1000:"S8\r"}
        print "Reseting USB2-F-7x01"
        self.ser.write("R\r")
        try:
            result = self._readResponse()
        except DeviceTimeout:
            raise BusInitError("Timeout waiting for USB2-F-7x01")
        except BusReadError:
            raise BusInitError("Unable to Reset USB2-F-7x01")
        time.sleep(2)

        print "Setting Bit Rate"
        self.ser.write(bitrates[self.bitrate])
        try:
            result = self._readResponse()
        except DeviceTimeout:
            raise BusInitError("Timeout waiting for USB2-F-7x01")
        except BusReadError:
            raise BusInitError("Unable to set CAN Bit rate")

    def open(self):
        print "Opening CAN Port"
        self.ser.write("O\r")
        try:
            result = self._readResponse()
        except DeviceTimeout:
            raise BusInitError("Timeout waiting for USB2-F-7x01")
        except BusReadError:
            raise BusInitError("Unable to Open CAN Port")

    def close(self):
        print "Closing CAN Port"
        self.ser.write("C\r")
        try:
            result = self._readResponse()
        except DeviceTimeout:
            raise BusInitError("Timeout waiting for USB2-F-7x01")
        except BusReadError:
            raise BusInitError("Unable to Close CAN Port")

    def sendFrame(self, frame):
        if frame['id'] < 0 or frame['id'] > 2047:
            raise ValueError("Frame ID out of range")
        xmit = "t"
        xmit = xmit + '%03X' % (frame['id'])
        xmit = xmit + str(len(frame['data']))
        for each in frame['data']:
            xmit = xmit + '%02X' % (each)
        xmit = xmit + '\r'
        self.ser.write(xmit)
        try:
            result = self._readResponse()
        except DeviceTimeout:
            raise BusWriteError("Timeout waiting for USB2-F-7x01")
        if result != 'z\r':
            raise BusWriteError("Bad response from USB2-F-7x01")


    def recvFrame(self):
        result = self._readResponse()
        return result


class Connection():
    """Class that represents a connection to a CAN device"""
    def __init__(self, portname = "", bitrate = 125, timeout = 0.5):
        self.portname = portname
        self.timeout = timeout
        self.devices = []
        self.devices.append(EasyDevice(bitrate))

    def connect(self):
        #This code tries to find a USB/CAN device on one of the comm ports.
        if self.portname == "":
            for each in comports():
                if string.find(each[1], "USB2-F-7x01") >= 0:
                    self.portname = each[0]
                    print "Found CAN device on Port", self.portname

        if self.portname == "":
            raise BusInitError("No CAN device found")

        self.ser = serial.Serial(self.portname, 115200, timeout=self.timeout)
        self.devices[0].setport(self.ser)
        self.init = self.devices[0].init
        self.open = self.devices[0].open
        self.close = self.devices[0].close
        self.sendFrame = self.devices[0].sendFrame
        self.recvFrame = self.devices[0].recvFrame


if __name__ == '__main__':
    can = Connection("/dev/ttyUSB0")
    frame = {}
    can.connect()
    can.init()
    can.open()
    
    frames=[{'id':0x701, 'data':[0, 1, 3, 0x0F, 0x00]},
            {'id':0x701, 'data':[0, 1, 3, 0x0F, 0x01]},
            {'id':0x701, 'data':[0, 1, 3, 0x0F, 0x02]},
            {'id':0x701, 'data':[0, 1, 3, 0x0F, 0x03]},
            {'id':0x701, 'data':[0, 1, 3, 0x0F, 0x04]},
            {'id':0x701, 'data':[0, 1, 3, 0x0F, 0x05]},
            {'id':0x701, 'data':[0xFF, 7, 1, 0xF7, 0x00]},
            {'id':0x6E0, 'data':[1, 0, 0, 0]},
            {'id':0x6E0, 'data':[2, 0, 0, 0]},
            {'id':0x6E0, 'data':[3, 0, 0, 0]},
            {'id':0x6E0, 'data':[4]},
            {'id':0x6E0, 'data':[5, 0, 0, 0, 0]}]

    for each in frames:
        can.sendFrame(each)
        try:
            result = can.recvFrame()
        except DeviceTimeout:
            result = "Timeout"
        print result
