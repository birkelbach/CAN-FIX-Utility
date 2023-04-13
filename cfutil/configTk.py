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

import logging
import logging.config
import cfutil.config as config
from . import nodes
from . import connection
import tkinter as tk
import tkinter.ttk as ttk

log = logging.getLogger(__name__)

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

class ConfigTree(ttk.Treeview):
    def __init__(self, parent, *args, **kwargs):
        ttk.Treeview.__init__(self, parent, *args, columns=('key', 'description', 'value', 'units'), selectmode='browse', show='headings', **kwargs)
        self['columns'] = ('key', 'description', 'value', 'units')
        self.column('key', width=40, stretch=False)
        self.heading('key', text='Key')
        self.column('description', stretch='True')
        self.heading('description', text='Description')
        self.column('value', width=40, anchor='w')
        self.heading('value', text='Value')
        self.column('units', width=40, anchor='w')
        self.heading('units', text='Units')



# Dialog box used to get information from the user regarding the
# python-can connection that we wish to make.
class ConfigDialog(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.title("CANFiX Configuration Utility - Config")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        mainFrame = ttk.Frame(self) # main form where we put the interface and dynamic widgets
        mainFrame.grid(column=0,row=0,sticky=tk.NSEW)
        mainFrame.grid_rowconfigure(0, weight=1)
        mainFrame.grid_columnconfigure(0, weight=1)

        treeView = ConfigTree(mainFrame)
        treeView.grid(column=0, row=0, sticky=tk.NSEW)

        sb = ttk.Scrollbar(mainFrame, command=treeView.yview)
        sb.grid(column=1, row=0, sticky=tk.NS)
        treeView.configure(yscrollcommand=sb.set)

        btnFrame = ttk.Frame(self) # Frame for the buttons.
        btnFrame.grid(column=0, row=1, sticky=tk.E)

        for n in range(20):
            treeView.insert('', 'end', values = [n, "item Number {}".format(n), 100-n, 'in'])

        # cancel and ok buttons
        btnCancel = ttk.Button(btnFrame, text="Close", command=self.close_mod)
        btnCancel.grid(row=0, column=0, sticky=tk.SE, padx=4, pady=4)
        btnOk = ttk.Button(btnFrame, text="Send", command=self.btn_send)
        btnOk.grid(row=0, column=1, sticky=tk.SE, padx=4, pady=4)

        self.protocol("WM_DELETE_WINDOW", self.close_mod)
        self.grab_set() # makes the dialog modal


    # send button callback.
    def btn_send(self):
        print("Send")

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
