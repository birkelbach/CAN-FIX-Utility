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

import json
from collections import OrderedDict


d =  {
  "name":"MakerPlane Switch Input",
  "type":"0x23",
  "model":"0x770001",
  "version":"0x01",
  "firmware_code":"0xF23",
  "firmware_driver":"STM32",
  "parameters":
    [
      int("0x101", base=16),
      int("0x102", base=16),
      int("0x103", base=16),
      int("0x104", base=16),
      int("0x105", base=16),
      int("0x106", base=16),
      int("0x107", base=16),
      int("0x108", base=16),
      int("0x109", base=16),
      int("0x10A", base=16),
      int("0x10B", base=16),
      int("0x10C", base=16),
      int("0x10D", base=16),
      int("0x10E", base=16),
      int("0x10F", base=16),
      int("0x110", base=16),
      int("0x111", base=16),
      int("0x112", base=16),
      int("0x113", base=16),
      int("0x114", base=16),
      int("0x115", base=16),
      int("0x116", base=16),
      int("0x117", base=16),
      int("0x11C", base=16),
      int("0x11D", base=16),
      int("0x11E", base=16),
      int("0x11F", base=16),
      int("0x120", base=16),
      int("0x121", base=16),
      int("0x122", base=16),
      int("0x123", base=16),
      int("0x308", base=16),
      int("0x309", base=16),
      int("0x30A", base=16),
      int("0x30B", base=16),
      int("0x30C", base=16),
      int("0x30D", base=16),
      int("0x30E", base=16),
      int("0x30F", base=16)
    ]
    }


configuration = []
key = 1

for x in range(12):
    c = OrderedDict()
    c["key"] = key
    c["name"] = "Input {} Selection".format(x+1)
    c["type"] = "UINT"
    c["input"] =  "list"
    sel = OrderedDict()
    sel["Flap Control Switches Pilot 1"] =           int("0x100", base=16)
    sel["Flap Control Switches Pilot 2"] =           int("0x101", base=16)
    sel["Trim Switch Pilot 1"] =                     int("0x102", base=16)
    sel["Trim Switch Pilot 2"] =                     int("0x103", base=16)
    sel["Electrical Bus Switches Pilot 1"] =         int("0x104", base=16)
    sel["Electrical Bus Switches Pilot 2"] =         int("0x105", base=16)
    sel["Lighting Switches Pilot 1"] =               int("0x106", base=16)
    sel["Lighting Switches Pilot 2"] =               int("0x107", base=16)
    sel["Fuel Pump Switches Pilot 1"] =              int("0x108", base=16)
    sel["Fuel Pump Switches Pilot 2"] =              int("0x109", base=16)
    sel["Fuel Valve Switches Pilot 1"] =             int("0x10A", base=16)
    sel["Fuel Valve Switches Pilot 2"] =             int("0x10B", base=16)
    sel["Auto Pilot Commands Pilot 1"] =             int("0x10C", base=16)
    sel["Auto Pilot Commands Pilot 2"] =             int("0x10D", base=16)
    sel["VHF Commands Pilot 1"] =                    int("0x10E", base=16)
    sel["VHF Commands Pilot 2"] =                    int("0x10F", base=16)
    sel["VOR/LOC Commands Pilot 1"] =                int("0x110", base=16)
    sel["VOR/LOC Commands Pilot 2"] =                int("0x111", base=16)
    sel["Transponder Commands Pilot 1"] =            int("0x112", base=16)
    sel["Transponder Commands Pilot 2"] =            int("0x113", base=16)
    sel["Starter / Magneto Commands Pilot 1"] =      int("0x114", base=16)
    sel["Starter / Magneto Commands Pilot 2"] =      int("0x115", base=16)
    sel["Landing Gear Commands Pilot 1"] =           int("0x116", base=16)
    sel["Landing Gear Commands Pilot 2"] =           int("0x117", base=16)
    sel["Landing Gear Commands Pilot 1"] =           int("0x116", base=16)
    sel["Landing Gear Commands Pilot 2"] =           int("0x117", base=16)
    sel["Generic Switches 1 (High Priority)"] =      int("0x11C", base=16)
    sel["Generic Switches 2 (High Priority)"] =      int("0x11D", base=16)
    sel["Generic Switches 3 (High Priority)"] =      int("0x11E", base=16)
    sel["Generic Switches 4 (High Priority)"] =      int("0x11F", base=16)
    sel["Generic Switches 5 (High Priority)"] =      int("0x120", base=16)
    sel["Generic Switches 6 (High Priority)"] =      int("0x121", base=16)
    sel["Generic Switches 7 (High Priority)"] =      int("0x122", base=16)
    sel["Generic Switches 8 (High Priority)"] =      int("0x123", base=16)
    sel["Generic Switches 1 (Normal Priority)"] =    int("0x308", base=16)
    sel["Generic Switches 2 (Normal Priority)"] =    int("0x309", base=16)
    sel["Generic Switches 3 (Normal Priority)"] =    int("0x30A", base=16)
    sel["Generic Switches 4 (Normal Priority)"] =    int("0x30B", base=16)
    sel["Generic Switches 5 (Normal Priority)"] =    int("0x30C", base=16)
    sel["Generic Switches 6 (Normal Priority)"] =    int("0x30D", base=16)
    sel["Generic Switches 7 (Normal Priority)"] =    int("0x30E", base=16)
    sel["Generic Switches 8 (Normal Priori] = y)"] = int("0x30F", base=16)
    c["selections"] = sel
    configuration.append(c)

# Dependent Key for each input
    key += 1

    c = { "key":key,
          "depends":{
              "key":key-1,
              "definitions":[
                  {
                  "compare":[int("0x100", base=16),
                             int("0x101", base=16)],
                  "name":"Flap Switch",
                  "type":"UINT",
                  "input":"list",
                  "selections":
                      {
                      "Up":0,
                      "Down":1,
                      "Position 1":2,
                      "Position 2":3,
                      "Position 3":4,
                      "Position 4":5,
                      "Position 5":6,
                      "Position 6":7
                      }
                  },
                  {
                  "compare":[int("0x102", base=16),
                             int("0x103", base=16)],
                  "name":"Trim Switch",
                  "type":"UINT",
                  "input":"list",
                  "selections":
                      {
                      "Pitch Up":0,
                      "Pitch Down":1,
                      "Pitch Center":2,
                      "Roll Left":3,
                      "Roll Right":4,
                      "Roll Center":5,
                      "Yaw Left":6,
                      "Yaw Right":7,
                      "Yaw Center":8,
                      "Collective Up":9,
                      "Collective Dn":10,
                      "AT Pedals Left":11,
                      "AT Pedals Right":12,
                      "AT Pedals Center":13
                      }
                  },
                  {
                  "compare":[
                      int("0x104", base=16),
                      int("0x105", base=16),
                      int("0x106", base=16),
                      int("0x107", base=16),
                      int("0x108", base=16),
                      int("0x109", base=16),
                      int("0x10A", base=16),
                      int("0x10B", base=16)
                      ],
                   "name":"Switch Number",
                   "type":"UINT",
                   "min":0,
                   "max":7
                  },
                  {
                  "compare":[int("0x10C", base=16),
                             int("0x10D", base=16)],
                  "name":"Autopilot Function",
                  "type":"UINT",
                  "input": "list",
                  "selections":
                      {
                      "Engage":0,
                      "Disconnect":1,
                      "VS Mode":2,
                      "Alt Hold Mode":3,
                      "Alt Select Mode":4,
                      "Heading Increment":5,
                      "Heading Decrement":6,
                      "Custom Command 1":7,
                      "Custom Command 2":8,
                      "Custom Command 3":9,
                      "Custom Command 4":10,
                      "Custom Command 5":11,
                      "Custom Command 6":12,
                      "Custom Command 7":13,
                      "Custom Command 8":14,
                      "Custom Command 9":15
                      }
                  },
                  {
                  "compare":[int("0x10E", base=16),
                             int("0x10F", base=16)],
                  "name":"VHF Command",
                  "type":"SHORT",
                  "input": "list",
                  "selections":
                      {
                      "PTT":0,
                      "Flip":1,
                      "Next Saved Frequency":2,
                      "Prev Saved Frequency":3
                      }
                  },
                  {
                  "compare":[int("0x10E", base=16),
                             int("0x10F", base=16)],
                  "name":"VHF Command",
                  "type":"SHORT",
                  "input":"list",
                  "selections":
                      {
                      "PTT":0,
                      "Flip":1,
                      "Next Saved Frequency":2,
                      "Prev Saved Frequency":3
                      }
                  },
                  {
                  "compare":[int("0x110", base=16),
                             int("0x111", base=16)],
                  "name":"VOR / Loc Command",
                  "type":"SHORT",
                  "input":"list",
                  "selections":
                      {
                      "Flip":0,
                      "Next Saved Frequency":1,
                      "Prev Saved Frequency":2
                      }
                  },
                  {
                  "compare":[int("0x112", base=16),
                             int("0x113", base=16)],
                  "name":"Transponder Command",
                  "type":"SHORT",
                  "input":"list",
                  "selections":
                      {
                      "IDENT":0,
                      "ALT":1,
                      "STBY":2,
                      "VFR":3,
                      "OFF":4,
                      "Squat Switch":5
                      }    
                  },
                  {
                  "compare":[int("0x114", base=16),
                             int("0x125", base=16)],
                  "name":"Switch Number",
                  "type":"SHORT",
                  "min":0,
                  "max":7    
                  },
                  {
                  "compare":[
                      int("0x11C", base=16),
                      int("0x11D", base=16),
                      int("0x11E", base=16),
                      int("0x11F", base=16),
                      int("0x120", base=16),
                      int("0x121", base=16),
                      int("0x122", base=16),
                      int("0x123", base=16),
                      int("0x308", base=16),
                      int("0x309", base=16),
                      int("0x30A", base=16),
                      int("0x30B", base=16),
                      int("0x30C", base=16),
                      int("0x30D", base=16),
                      int("0x30E", base=16),
                      int("0x30F", base=16)
                      ],
                  "name":"Switch Number",
                  "type":"SHORT",
                  "min":0,
                  "max":39    
                  }
              ]
         }
    }

    configuration.append(c)
    key += 1

    d["configuration"] = configuration
s = json.dumps(d, indent = 4)
print(s)