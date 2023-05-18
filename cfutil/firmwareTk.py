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
from . import firmware
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
import threading

log = logging.getLogger(__name__)

class FirmwareThread(threading.Thread):
    def __init__(self, fw):
        super(FirmwareThread, self).__init__()
        self.fw = fw
        self.error = ""

    def run(self):
        try:
            self.fw.download()
        except firmware.FirmwareError as e:
            log.error(e)
            self.error = str(e)



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



# Dialog box used to get information from the user regarding the
# python-can connection that we wish to make.
class FirmwareDialog(tk.Toplevel):
    def __init__(self, parent, nodelist, node, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.title("CANFiX Configuration Utility - Upload Firmware")
        self.nodelist = nodelist
        self.node = node
        self.uploading = False
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        mainframe = tk.Frame(self) # main form where we put the interface and dynamic widgets
        mainframe.grid_rowconfigure(5, weight=1)
        mainframe.grid_columnconfigure(1, weight=1)
        mainframe.grid(column = 0, row=0, padx=2, pady=2, sticky = tk.NSEW)
        buttonframe = tk.Frame(self) # Frame for the buttons.
        buttonframe.grid_rowconfigure(0, weight=1)
        buttonframe.grid_columnconfigure(0, weight=1)
        buttonframe.grid(column=0, row=1, padx=2, pady=2, sticky=tk.EW)


        nl = {}
        for each in self.nodelist:
            if each is not None:
                nl[each.name] = each.nodeid

        l = tk.Label(mainframe, text="Node")
        l.grid(row=0, column=0, sticky=tk.E, pady = 2, padx = 5)
        self.nodeselect = NodeSelect(mainframe, nl)
        self.nodeselect.bind("<<ComboboxSelected>>", self.node_selected)
        self.nodeselect.value = node
        self.nodeselect.grid(row=0, column=1, sticky=tk.EW, pady = 2, padx = 5, columnspan=2)

        l = tk.Label(mainframe, text="Driver")
        l.grid(row=1, column=0, sticky=tk.E, pady = 2, padx = 5)
        self.driverselect = ttk.Combobox(mainframe)
        self.driverselect['values'] = [k for k in firmware.GetDriverList()]
        self.driverselect.grid(row=1, column=1, sticky=tk.EW, pady = 2, padx = 5, columnspan=2)

        l = tk.Label(mainframe, text="ID Code")
        l.grid(row=2, column=0, sticky=tk.E, pady = 2, padx = 5)
        self.codetext = tk.StringVar()
        self.codeentry = ttk.Entry(mainframe, textvariable=self.codetext)
        self.codeentry.grid(row=2, column=1, sticky=tk.EW, pady = 2, padx = 5, columnspan=2)

        self.node_selected(0) # Value doesn't matter the function gets it from the widget

        l = tk.Label(mainframe, text="Arguments")
        l.grid(row=3, column=0, sticky=tk.E, pady = 2, padx = 5)
        self.argtext = tk.StringVar()
        self.argentry = ttk.Entry(mainframe, textvariable=self.argtext)
        self.argentry.grid(row=3, column=1, sticky=tk.EW, pady = 2, padx = 5, columnspan=2)


        l = tk.Label(mainframe, text="Filename")
        l.grid(row=4, column=0, sticky=tk.E, pady = 2, padx = 5)
        self.filename = tk.StringVar()
        fileentry = ttk.Entry(mainframe, textvariable=self.filename)
        fileentry.grid(row=4, column=1, sticky=tk.EW, pady = 5, padx = 5)
        brownsebtn = ttk.Button(mainframe, text="Browse", command=self.get_filename)
        brownsebtn.grid(row=4, column=2, padx=2, pady=2, sticky=tk.E)

        # Download Progress Frame
        f = ttk.Frame(mainframe)
        f['borderwidth'] = 1
        f['relief'] = 'sunken'
        f.grid_rowconfigure(0, weight=1)
        f.grid_columnconfigure(0, weight=1)
        f.grid(row=5, column=0, pady = 2, padx = 2, columnspan=3, sticky=tk.NSEW)
        self.progressLabel = tk.Label(f, text="Waiting...")
        self.progressLabel.grid(row=0, column=0, sticky=tk.W)
        self.progressVariable = tk.IntVar()
        self.progressBar = ttk.Progressbar(f, orient='horizontal', length='300', mode='determinate', variable=self.progressVariable)
        self.progressBar.grid(row=1, column=0, sticky=tk.EW)

        # cancel and ok buttons
        btn1 = ttk.Button(buttonframe, text="Close", command=self.close_mod)
        btn1.grid(row=0, column=0, padx=2, pady=2, sticky=tk.SE)
        self.uploadButton = ttk.Button(buttonframe, text="Upload", command=self.btn_upload)
        self.uploadButton.grid(row=0, column=1, padx=2, pady=2, sticky=tk.SE)

        self.protocol("WM_DELETE_WINDOW", self.close_mod)
        self.grab_set() # makes the dialog modal

    def node_selected(self, value):
        if self.nodeselect.value is None: return # Do Nothing

        node = self.nodelist[self.nodeselect.value]
        if node is not None:
            self.driverselect.set(node.device.fwDriver)
            self.codetext.set(node.device.fwUpdateCode)

    # Called periodically during the download to update the status
    # and the progress
    def update(self):
        self.progressLabel.configure(text = self.fw.status)
        self.progressVariable.set(int(self.fw.progress*100))
        if self.fwThread.error:
            #messagebox.showerror("Firmware Problem", self.fwThread.error)
            self.downloadEnded()
            self.progressLabel.configure(text = self.fwThread.error)
            self.progressVariable.set(0)
        if self.uploading:
            self.after(100, self.update)
        if self.fw.progress >= 1.0:
            self.downloadEnded()


    def get_filename(self):
        filetypes = (
            ('firmware', '*.cfw'),
            ('firmware', '*.tar.gz'),
            ('firmware', '*.bin'),
            ('All files', '*.*')
        )
        filename = filedialog.askopenfilename(title="Open Firmware File",
                                              filetypes=filetypes)
        self.filename.set(filename)

    # Cleans up after the download is over.  Also the stop callback from the firmware driver
    def downloadEnded(self):
        if self.uploading: # This will keep us from doing this twice
            self.fwThread.join(timeout=1.0)
            connection.canbus.free_connection(self.fw.can)
            self.uploadButton.configure(command = self.btn_upload, text = "Upload")
            self.uploading = False

    # upload button callback.  Launch the firmware thread and disable the upload button
    def btn_upload(self):
        conn = connection.canbus.get_connection()
        try:
            self.fw = firmware.Firmware(self.driverselect.get(), self.filename.get(), self.nodeselect.value, int(self.codetext.get()), conn)
        except Exception as e:
            self.progressLabel.configure(text = e)
            return
        self.fw.setStopCallback(self.downloadEnded)
        self.fwThread = FirmwareThread(self.fw)
        self.fwThread.start()
        self.uploadButton.configure(command = self.btn_cancel, text = "Cancel")
        self.uploading = True
        self.after(100, self.update)

    def btn_cancel(self):
        self.fw.stop()

    def close_mod(self):
        # top right corner cross click: return value ;`x`;
        # we need to send it a value, otherwise there will be an exception when closing parent window
        if not self.uploading:
            # Check the status of a firmware download.
            self.returning = ";`x`;"
            self.quit()

if __name__ == "__main__":
    pass

# TODO:
#    Make the dialog default to the previous set of interface/arguments
#    Dialog opening position and size
