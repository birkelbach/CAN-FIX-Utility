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

# Dialog box used to get information from the user regarding the
# python-can connection that we wish to make.
class ParamInfoDialog(tk.Toplevel):
    def __init__(self, parent, par, nodethread, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        if isinstance(par, int):
            pid = par
            idx = 0
        else:
            pid, idx = par.split('.')
            pid = int(pid)
            idx = int(idx)
        self.par = nodethread.parameterlist[(pid,idx)]
        self.title("CANFiX Configuration Utility - Parameter {}".format(par))
        g = settings.get("paraminfo_geometry")
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

        style = ttk.Style()
        style.configure("Mystyle.Treeview",  indent=15 , bd=0)
        style.layout("Mystyle.Treeview", [('Mystyle.Treeview.treearea', {'sticky': 'nswe'})]) # Remove the borders

        self.infoView = ttk.Treeview(infoframe, columns=["value"], style="Mystyle.Treeview")
        self.infoView.grid(row=0, column=0, sticky=tk.NSEW)
        infoScroll = ttk.Scrollbar(infoframe, command=self.infoView.yview)
        infoScroll.grid(row=0, column=1, sticky=tk.NS)
        self.infoView['yscrollcommand'] = infoScroll.set
        self.infoView.column('#0', width=180, stretch=False)
        self.infoView.column('value', stretch=True)

        # Close button
        btn1 = ttk.Button(buttonframe, text="Close", command=self.close_mod)
        btn1.grid(row=0, column=0, sticky=tk.E)

        self.infoView.insert("", tk.END, iid="name", text="Name", values=[self.par.name])
        self.infoView.insert("", tk.END, iid="nid", text="Node" , values=[self.par.nodeid])
        self.infoView.insert("", tk.END, iid="pid", text="ID" , values=[self.par.pid])
        self.infoView.insert("", tk.END, iid="index", text="Index Number" , values=[self.par.index])
        self.infoView.insert("", tk.END, iid="type", text="Data Type" , values=[self.par.type])
        self.infoView.insert("", tk.END, iid="value", text="Value" , values=[self.par.value])
        self.infoView.insert("", tk.END, iid="units", text="Units" , values=[self.par.units])
        self.infoView.insert("", tk.END, iid="quality", text="Quality" , values=[str('Q' in self.par.quality)])
        self.infoView.insert("", tk.END, iid="fail", text="Failed" , values=[str('F' in self.par.quality)])
        self.infoView.insert("", tk.END, iid="annunciate", text="Annunciate" , values=[str('A' in self.par.quality)])
        self.infoView.insert("", tk.END, iid="meta", text="Meta Data" , values=[""], open=True)
        for v in self.par.meta:
            self.infoView.insert("meta", tk.END, open=True, iid=f"meta{v}", text=v ,values=[self.par.meta[v]])

        self.bind("<Escape>", self.close_mod)

        self.protocol("WM_DELETE_WINDOW", self.close_mod)
        self.grab_set() # makes the dialog modal


    def close_mod(self, e=None):
        settings.set("paraminfo_geometry", self.geometry())
        # top right corner cross click: return value ;`x`;
        # we need to send it a value, otherwise there will be an exception when closing parent window
        self.returning = ";`x`;"
        self.quit()

if __name__ == "__main__":
    pass


