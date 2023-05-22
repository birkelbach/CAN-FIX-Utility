#!/usr/bin/env python3
#  CAN-FIX Utilities - An Open Source CAN FIX Utility Package
#  Copyright (c) 2023 Phil Birkelbach
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

import tkinter as tk
import tkinter.ttk as ttk

# each of these classes is a specific tkinter widget that handles
# retrieving the specific type of information.  The value property
# is used to set / get the value shown.  This might simply wrap the
# underlying .get() method or it may do something more complex.  The
# value returned from these objects should be suitable as arguments to
# the python-can Bus() class constructor.
class NodeSelect(ttk.Combobox):
    def __init__(self, parent, nodelist, *args, **kwargs):
        ttk.Combobox.__init__(self, parent, *args, **kwargs)

        self.nodelist = {}
        for name, id in nodelist.items():
            self.nodelist[f"{id}, {name}"] = id

        self['values'] = [k for k in self.nodelist]

    # Value is the node number of the selected node
    # It can be either entered directly or the node selected by name
    @property
    def value(self):
        s = self.get()
        if s in self.nodelist:
            x = self.nodelist[s]
        else:
            try:
                x = int(s)
                if x < 1 or x > 255: x = None
            except:
                x = None
        return x

    @value.setter
    def value(self, v):
        try:
            for name, id in self.nodelist.items():
                if v == id:
                    self.set(name)
                    return
            self.set(str(int(v)))
        except:
           self.set("")
