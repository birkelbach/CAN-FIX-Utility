#!/usr/bin/env python3

import time
import can

bustype = 'socketcan'
channel = 'vcan0'
# rx_id = 0x72A
# tx_id = 0x72B
nodeid = 0xB3

bus = can.interface.Bus(channel=channel, bustype=bustype)
while(True):
    #msg = can.Message(arbitration_id=0xfee, data=[id, i, 0, 1, 3, 1, 4, 1], extended_id=False)
    #    bus.send(msg)
    # Issue #3: Need to keep running to ensure the writing threads stay alive. ?
    #time.sleep(0)
    msg = bus.recv(0.5)
    if msg is not None:
        # TODO: Get the channel number out of this
        if msg.data == bytearray([7,nodeid,0xb3,0x07,00]):
            print("There it is")
            break
        else:
            print(list(msg.data))
            print("Nope that ain't it")

msg.data = bytearray([7,msg.arbitration_id - 0x6E0, 0x00])
msg.arbitration_id = 0x6E0 + nodeid
msg.dlc=3
bus.send(msg)

address = 0xFFFFFFFF
length = 0
offset = 0
count = 0
getout = False

while(getout == False):
    msg = bus.recv(1)

    if address == 0xFFFFFFFF: # This means that we are waiting for a command
        if msg is not None:
            if msg.arbitration_id != 0x7E0 + 0: # replace with our channel
                print("{:02X} Not our channel".format(msg.arbitration_id))
                continue
            address = msg.data[1] + (msg.data[2]<<8) + (msg.data[3]<<16) + (msg.data[4]<<24)
            #print("Address = {}".format(address))
            if msg.data[0] == 0x01:
                length = msg.data[5] + (msg.data[6]<<8)
                print( "Write Buffer {0}, length {1}".format(address,length))
            elif msg.data[0] == 0x02:
                print( "Erase Page {0}".format(address))
                address = 0xFFFFFFFF
            elif msg.data[0] == 0x03:
                print( "Write Page {0}".format(address))
                address = 0xFFFFFFFF
            elif msg.data[0] == 0x04:
                print( "Abort")
                address = 0xFFFFFFFF
            elif msg.data[0] == 0x05:
                print( "Complete")
                getout = True
            msg.arbitration_id = msg.arbitration_id + 1
            #time.sleep(0.1)
            bus.send(msg)
        else: #Timeout
            count += 1
            if count > 30:
                count = 0
                break

    else:
        if msg is not None:
            #print("[{}: ".format(offset), end='')
            offset += msg.dlc
            #for each in list(msg.data):
            #    print("{:02X} ".format(each), end='')
            #print("]")
            msg.arbitration_id = msg.arbitration_id + 1
            msg.data[0] = offset & 0xFF
            msg.data[1] = (offset & 0xFF00)>>8
            msg.dlc=2
            bus.send(msg)
            if offset >= length:
                address = 0xFFFFFFFF
                offset = 0
        else:
            count += 1
            if count > 30:
                count = 0
                break
