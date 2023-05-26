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
import json
import os
from . import configNode
from . import settings
from cfutil.widgets import NodeSelect
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox

log = logging.getLogger(__name__)

class LoadError(Exception):
    pass

class SaveError(Exception):
    pass


# Dialog box used to get information from the user regarding the
# python-can connection that we wish to make.
class LoadSaveDialog(tk.Toplevel):
    def __init__(self, parent, node, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)

        self.done = False
        self.status = ""
        self.progress = 0
        self.node = node
        if self.box_type == "LOAD":
            self.title("Load Configuration")
        else:
            self.title("Save Configuration")
        g = settings.get("loadsave_geometry")
        if g:
            self.geometry(g)

        #self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        mainFrame = ttk.Frame(self) # main form where we put the interface and dynamic widgets
        mainFrame.grid(column=0,row=0,sticky=tk.NSEW, padx=2, pady=2, columnspan=10)
        mainFrame.grid_rowconfigure(0, weight=1)
        mainFrame.grid_columnconfigure(0, weight=1)

        nl = {}
        for each in self.nodelist:
            if each is not None:
                nl[each.name] = each.nodeid

        l = tk.Label(mainFrame, text="Node")
        l.grid(row=0, column=0, sticky=tk.W, pady = 2, padx = 5, columnspan=2)
        self.nodeselect = NodeSelect(mainFrame, nl)
        self.nodeselect.value = self.node
        self.nodeselect.grid(row=1, column=0, padx=4, pady=4, sticky=tk.EW, columnspan=2)

        l = ttk.Label(mainFrame, text = 'Select Configuration File')
        l.grid(row=2, column=0, padx=4, pady=4, sticky=tk.W)
        self.filenameVar = tk.StringVar()
        self.fileEntry = ttk.Entry(mainFrame, textvariable=self.filenameVar)
        self.fileEntry.grid(row=3, column=0, padx=4, pady=4, sticky=tk.NSEW)
        btnBrowse = ttk.Button(mainFrame, text="Browse", command=self.file_select, underline=0)
        btnBrowse.grid(row=3, column=1, sticky=tk.SE, padx=4, pady=4)

        self.progressVariable = tk.IntVar()
        self.progressBar = ttk.Progressbar(mainFrame, orient='horizontal', length='300', mode='determinate', variable=self.progressVariable)
        self.progressBar.grid(row=4, column=0, padx=8, pady=8, sticky=tk.EW, columnspan=2)

        self.statusLabel = ttk.Label(mainFrame, text = self.status)
        self.statusLabel.grid(row=5, column=0, padx=4, pady=4, sticky=tk.W)

        # cancel and 'go' buttons
        btnCancel = ttk.Button(self, text="Close", command=self.close_mod, takefocus=0)
        btnCancel.grid(row=1, column=0, sticky=tk.SE, padx=4, pady=4)
        if self.box_type == "LOAD":
            fn = settings.get("last_load_file")
            if fn: self.filenameVar.set(fn)
            btnText = "Send"
        else:
            fn = settings.get("last_save_file")
            if fn: self.filenameVar.set(fn)
            btnText = "Save"
        btnStart = ttk.Button(self, text=btnText, command=self.btn_apply, underline=0, takefocus=0)
        btnStart.grid(row=1, column=1, sticky=tk.SE, padx=4, pady=4)

        self.bind("<Control-b>", self.file_select)
        self.bind("<Escape>", self.close_mod)

        self.protocol("WM_DELETE_WINDOW", self.close_mod)
        self.grab_set() # makes the dialog modal

    def file_select(self, e=None):
        filetypes = (
            ('json files', '*.json'),
            ('All files', '*.*')
        )
        dn = os.path.dirname(self.filenameVar.get())
        if self.box_type == "LOAD":
            filename = filedialog.askopenfilename(filetypes=filetypes, initialfile=self.filenameVar.get(), initialdir = dn)
        else:
            filename = filedialog.asksaveasfilename(filetypes=filetypes, initialdir=dn)
        if filename:
            self.filenameVar.set(filename)

    def update(self):
        self.statusLabel.configure(text = self.status)
        self.progressVariable.set(int(self.progress))

        if self.thread.is_alive():
            self.after(100, self.update)
        else:
            self.thread.join()
            self.file.close()

    def set_status(self, s):
        self.status = s

    def set_progress(self, p):
        self.progress = p

    def close_mod(self, e=None):
        settings.set("loadsave_geometry", self.geometry())
        # top right corner cross click: return value ;`x`;
        # we need to send it a value, otherwise there will be an exception when closing parent window
        self.returning = ";`x`;"
        self.quit()


class LoadDialog(LoadSaveDialog):
    def __init__(self, parent, nodelist, node, *args, **kwargs):
        self.nodelist  = nodelist
        self.box_type = "LOAD"
        LoadSaveDialog.__init__(self, parent, node, *args, **kwargs)

    def btn_apply(self, e=None):
        self.file = open(self.filenameVar.get(), 'r')
        settings.set("last_load_file", self.filenameVar.get())
        if self.nodeselect.value is None:
            messagebox.showerror("Load Error", message="You must Supply a node id first")
            return
        else:
            try:
                self.thread = configNode.LoadThread(self.node, self.file)
            except json.decoder.JSONDecodeError as e:
                log.error(e)
                messagebox.showerror("JSON Error", message="Configuration Save file loading error")
                return

            self.thread.statusCallback = self.set_status
            self.thread.percentCallback = self.set_progress
            self.thread.start()
            self.after(100, self.update)


class SaveDialog(LoadSaveDialog):
    def __init__(self, parent, nodelist, node, *args, **kwargs):
        self.nodelist  = nodelist
        self.box_type = "SAVE"
        LoadSaveDialog.__init__(self, parent, node, *args, **kwargs)

    def btn_apply(self, e=None):
        self.file = open(self.filenameVar.get(), 'w')
        settings.set("last_save_file", self.filenameVar.get())
        if self.nodeselect.value is None:
            messagebox.showerror("Save Error", message="You must Supply a node id first")
            return
        else:
            self.thread = configNode.SaveThread(self.nodeselect.value, self.file)
            self.thread.statusCallback = self.set_status
            self.thread.percentCallback = self.set_progress
            self.thread.start()
            self.after(100, self.update)


if __name__ == "__main__":
    pass

