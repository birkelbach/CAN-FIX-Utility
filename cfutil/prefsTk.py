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

class pTab(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


# Dialog box used to set application preferences.
class PrefsDialog(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.title("CANFiX Configuration Utility - Preferences")
        g = settings.get("prefs_geometry")
        if g:
            self.geometry(g)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.nb = ttk.Notebook(self)

        appTab = pTab(self.nb)
        dataTab = pTab(self.nb)
        nodesTab = pTab(self.nb)

        self.nb.add(nodesTab, text="Nodes")
        self.nb.add(dataTab, text="Data")
        self.nb.add(appTab, text="App")

        self.nb.grid(row=0, column=0, sticky=tk.NSEW)

        buttonframe = tk.Frame(self) # Frame for the buttons.
        buttonframe.grid_rowconfigure(0, weight=1)
        buttonframe.grid_columnconfigure(0, weight=1)
        buttonframe.grid(column=0, row=1, padx=2, pady=2, sticky=tk.EW)

        # Close Button
        closeButton = ttk.Button(buttonframe, text="Close", command=self.close_mod)
        closeButton.grid(row=0, column=0, padx=2, sticky=tk.E)
        # Apply Button
        applyButton = ttk.Button(buttonframe, text="Apply", command=self.apply)
        applyButton.grid(row=0, column=1, padx=2, sticky=tk.E)

        self.bind("<Escape>", self.close_mod)

        self.protocol("WM_DELETE_WINDOW", self.close_mod)
        self.grab_set() # makes the dialog modal

    def apply(self):
        print("Apply")

    def close_mod(self, e=None):
        # top right corner cross click: return value ;`x`;
        # we need to send it a value, otherwise there will be an exception when closing parent window
        settings.set("prefs_geometry", self.geometry())
        self.returning = ";`x`;"
        self.quit()

if __name__ == "__main__":
    pass


