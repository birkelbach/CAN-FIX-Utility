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

import logging
import logging.config
import cfutil.config as config
from . import nodes
from . import connection
import tkinter as tk
import tkinter.ttk as ttk

log = logging.getLogger(__name__)

# each of these classes is a specific tkinter widget that handles
# retrieving the specific type of information.  The value property
# is used to set / get the value shown.  This might simply wrap the
# underlying .get() method or it may do something more complex.  The
# value returned from these objects should be suitable as arguments to
# the python-can Bus() class constructor.
class SocketCanChannel(ttk.Combobox):
    def __init__(self, parent, *args, **kwargs):
        ttk.Combobox.__init__(self, parent, *args, **kwargs)
        self['values'] = ['can0', 'can1','vcan0', 'vcan1', 'slcan0', 'slcan1']

    @property
    def value(self):
        print(self.get())
        return self.get()

class PCANChannel(ttk.Combobox):
    def __init__(self, parent, *args, **kwargs):
        ttk.Combobox.__init__(self, parent, *args, **kwargs)
        self['values'] = ['PCAN_USBBUS1']

    @property
    def value(self):
        return self.get()

class SerialChannel(ttk.Combobox):
    def __init__(self, parent, *args, **kwargs):
        ttk.Combobox.__init__(self, parent, *args, **kwargs)
        self['values'] = config.portlist

    @property
    def value(self):
        return self.get()

class SerialBaudrate(ttk.Combobox):
    def __init__(self, parent, *args, **kwargs):
        ttk.Combobox.__init__(self, parent, *args, **kwargs)
        self['values'] = [2400, 4800, 9600, 19200, 28800, 38400, 57600, 76800, 115200, 230400]
        self['state'] = 'readonly'

    @property
    def value(self):
        return self.get()

class Bitrate(ttk.Combobox):
    def __init__(self, parent, *args, **kwargs):
        ttk.Combobox.__init__(self, parent, *args, **kwargs)
        self['values'] = ['125 kbps', '250 kbps', '500 kbps', '1000 kbps']
        self['state'] = 'readonly'

    @property
    def value(self):
        return self.get()

class TextEntry(tk.Entry):
    def __init__(self, parent, *args, **kwargs):
        tk.Entry.__init__(self, parent, *args, **kwargs)

    @property
    def value(self):
        return self.get()

class IntEntry(tk.Entry):
    def __init__(self, parent, *args, **kwargs):
        tk.Entry.__init__(self, parent, *args, **kwargs)

    @property
    def value(self):
        return self.get()

# This is a dictionary of the interfaces that we use for populating
# the dialog box.  The first item in the tuple is the label text,
# the second item is the argument name.  This argument should be suitable
# as the argument name for the given interface's python-can Bus class
# constructor.   The third is the class of the object that we'll use
interface_db = {}
interface_db['socketcan'] = [('Channel', 'channel', SocketCanChannel)]
interface_db['socketcand'] = [('Channel', 'channel', SocketCanChannel),
                              ('Host', 'host', TextEntry),
                              ('Port', 'post', IntEntry)]
interface_db['slcan'] = [('Channel', 'channel', SerialChannel),
                         ('Baudrate', 'baudrate', SerialBaudrate),
                         ('Bitrate', 'bitrate', Bitrate)]
interface_db['pcan'] = [('Channel', 'channel', PCANChannel),
                         ('Device ID', 'devicd_id', IntEntry),
                         ('Bitrate', 'bitrate', Bitrate)]


# Dialog box used to get information from the user regarding the
# python-can connection that we wish to make.
class ConnectDialog(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.title("CANFiX Configuration Utility - Connect")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.interface = None # will be set to the interface text
        self.okay = False  # This will get set of the 'Ok' button is set
        self.frm1 = tk.Frame(self) # main form where we put the interface and dynamic widgets
        self.frm1.pack(ipadx=2, ipady=2, side=tk.TOP, fill=tk.BOTH, expand=True)
        frm2 = tk.Frame(self) # Frame for the buttons.
        frm2.pack(ipadx=2, ipady=2, side=tk.RIGHT, fill=tk.BOTH)
        # These are lists that we use to keep track of the dynamic widgets that
        # change when the user selects a differnet interfacd
        self.__labels = [None] * 20
        self.__widgets = [None] * 20
        # The widget to get the interface text is static and on top
        message = tk.Label(self.frm1, text="Interface")
        message.grid(row=0, column=0, sticky="W", pady = 2, padx = 5)
        self.interfaces = ttk.Combobox(self.frm1)
        i = config.interface
        if i is None:
            i = "socketcan"
        self.interfaces.set(i)
        self.interfaces['values'] = list(interface_db.keys())
        self.interfaces['state'] = 'readonly'
        self.interfaces.grid(row=0, column=1, sticky="W", pady = 2, padx = 5)
        self.interfaces.bind('<<ComboboxSelected>>', self.interface_change)
        # We call this here to set the interface specific widgets on the dialog
        self.interface_change(None)
        # cancel and ok buttons
        btn1 = ttk.Button(frm2, text="Cancel", command=self.close_mod)
        btn1.grid(row=0, column=0, sticky=tk.SE)
        btn2 = ttk.Button(frm2, text="Ok", command=self.btn_ok)
        btn2.grid(row=0, column=1, sticky=tk.SE)

        self.protocol("WM_DELETE_WINDOW", self.close_mod)
        self.grab_set() # makes the dialog modal

    # returns a dictionary that is suitable for use
    # in the python-can Bus class constructor
    @property
    def arguments(self):
        d = {}
        x = 0
        for each in interface_db[self.interface]:
            d[each[1]] = self.__widgets[x].get()
        return d

    # callback that changes the widgets that are shown
    # depending on the interface that's chosen
    def interface_change(self, event):
        if self.interface != self.interfaces.get():
            self.interface = self.interfaces.get()
        else:
            return # Don't do anything
        for x in range(len(self.__widgets)):
            if self.__widgets[x] is not None:
                self.__widgets[x].grid_forget()
                self.__widgets[x].destroy()
                self.__widgets[x] = None
            if self.__labels[x] is not None:
                self.__labels[x].grid_forget()
                self.__labels[x].destroy()
                self.__labels[x] = None

        wlist = interface_db[self.interface]
        for x in range(len(wlist)):
            self.__labels[x] = ttk.Label(self.frm1, text = wlist[x][0])
            self.__labels[x].grid(row=x+1, column=0, sticky="W", pady = 2, padx = 5)
            self.__widgets[x] = wlist[x][2](self.frm1)
            self.__widgets[x].grid(row=x+1, column=1, sticky="W", pady = 2, padx = 5)

    # ok button callback.  It just sets the okay flag and then calls close
    def btn_ok(self):
        self.okay = True
        self.close_mod()

    def close_mod(self):
        # top right corner cross click: return value ;`x`;
        # we need to send it a value, otherwise there will be an exception when closing parent window
        self.returning = ";`x`;"
        self.quit()

if __name__ == "__main__":
    pass

# TODO:
#    Make the dialog default to the previous set of interface/arguments
#    Dialog opening position and size
