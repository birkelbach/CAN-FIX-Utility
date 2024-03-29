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
from . import settings
import tkinter as tk
import tkinter.ttk as ttk

log = logging.getLogger(__name__)

# Dialog box used to show information about a particular node
class InfoDialog(tk.Toplevel):
    def __init__(self, parent, node, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.title("CANFiX Configuration Utility - Node {}".format(node.nodeid))
        g = settings.get("info_geometry")
        if g:
            self.geometry(g)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        infoframe = tk.Frame(self) # main form where we put the interface and dynamic widgets
        infoframe.grid_rowconfigure(0, weight=1)
        infoframe.grid_columnconfigure(0, weight=1)
        infoframe.grid(column = 0, row=0, padx=2, pady=2, sticky = tk.NSEW)
        buttonframe = tk.Frame(self) # Frame for the buttons.
        buttonframe.grid_rowconfigure(0, weight=1)
        buttonframe.grid_columnconfigure(0, weight=1)
        buttonframe.grid(column=0, row=1, padx=2, pady=2, sticky=tk.EW)

        self.infoView = ttk.Treeview(infoframe, columns=["value"])
        self.infoView.grid(row=0, column=0, sticky=tk.NSEW)
        infoScroll = ttk.Scrollbar(infoframe, command=self.infoView.yview)
        infoScroll.grid(row=0, column=1, sticky=tk.NS)
        self.infoView['yscrollcommand'] = infoScroll.set
        self.infoView.column('#0', width=200, stretch=True)
        self.infoView.column('value', stretch=True)

        l = ttk.Label(infoframe, text="Node Description:")
        l.grid(row=1, column=0, sticky=tk.W)
        self.textbox = tk.Text(infoframe, height=5, width=40)
        self.textbox.grid(row=2, column=0, sticky=tk.NSEW)
        scrollb = ttk.Scrollbar(infoframe, command=self.textbox.yview)
        scrollb.grid(row=2, column=1, sticky=tk.NS)
        self.textbox['yscrollcommand'] = scrollb.set

        # Close button
        btn1 = ttk.Button(buttonframe, text="Close", command=self.close_mod)
        btn1.grid(row=0, column=0, sticky=tk.E)

        self.infoView.insert("", tk.END, iid="deviceid", text="Device ID", values=[node.deviceid])
        self.infoView.insert("", tk.END, iid="nodeid", text="Node ID", values=[node.nodeid])
        self.infoView.insert("", tk.END, iid="model", text="Model Number", values=[node.model])
        self.infoView.insert("", tk.END, iid="version", text="Version", values=[node.version])
        self.infoView.insert("", tk.END, iid="status", text="Status", values=[node.status_str])

        self.textbox.insert('0.0', node.description)
        self.textbox['state'] = tk.DISABLED

        self.bind("<Escape>", self.close_mod)

        self.protocol("WM_DELETE_WINDOW", self.close_mod)
        self.grab_set() # makes the dialog modal


    def close_mod(self, e=None):
        # top right corner cross click: return value ;`x`;
        # we need to send it a value, otherwise there will be an exception when closing parent window
        settings.set("info_geometry", self.geometry())
        self.returning = ";`x`;"
        self.quit()

if __name__ == "__main__":
    pass


