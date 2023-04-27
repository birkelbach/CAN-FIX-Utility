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
from . import configNode
import tkinter as tk
import tkinter.ttk as ttk
import canfix

log = logging.getLogger(__name__)

# These are the custom widgets that we use for editing the configuration.  They
# are smart enough to deal with the types and min/max attributes of the key
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


class FloatEntry(tk.Entry):
    def __init__(self, parent, *args, **kwargs):
        tk.Entry.__init__(self, parent, *args, **kwargs)

    @property
    def value(self):
        return self.get()


class ListBox(ttk.Combobox):
    def __init__(self, parent, selections, *args, **kwargs):
        ttk.Combobox.__init__(self, parent, *args, **kwargs)
        self.selections = selections
        self["values"] = list(self.selections.keys())
    
    @property
    def value(self):
        return self.selections[self.get()]
    


# This is just a shortcut for storing the information for one configuration key
# There may be one of these associated with a configuration key or there may
# be many of them if the configuration key is dependent.
class ConfigControl():
    def __init__(self, item):
        if "compare" in item:
            self.compare = item["compare"]
        else:
            self.compare = None
        if "name" in item:
            self.name = item["name"]
        else:
            self.name = None
        if "type" in item:
            self.datatype = item["type"]
        else:
            self.datatype = "UINT" #default to 16 bit unsigned ?????
        if "input" in item:
            self.input = item["input"]
        else:
            self.input = "entry"
        if "min" in item:
            self.min = float(item["min"])
        else:
            self.min = 0
        if "max" in item:
            self.max = float(item["max"])
        else:
            self.max = 0
        if "multiplier" in item:
            self.multiplier = float(item["multiplier"])
        else:
            self.multiplier = 1.0
        if "units" in item:
            self.units = item["units"]
        else:
            self.units = ""
        if "selections" in item:
            self.selections = item["selections"]
        else:
            self.selections = []



# This is a record that we keep for each configuration key/value pair  We have
# a list of these in our ConfigTree class.  If we represent a dependent key
# then we'll have a list of ConfigControls and we'll select the proper one based
# on the parentValue that is passed.
class ConfigRecord():
    def __init__(self, item):
        self.key = item["key"]
        self.dirty = False    # Change to true if edited and not sent
        self.__parentValue = None
        self.dependentChildren = []
        if "depends" in item: # This configuration item is a dependent key
            self.dependent = True
            self.parentKey = item["depends"]["key"]
            self.definitions = []
            for each in item["depends"]["definitions"]:
                d = ConfigControl(each)
                self.definitions.append(d)
            self.control = None
        else:
            self.dependent = False
            self.control = ConfigControl(item)
            self.__value = 0

    @property
    def parentValue(self):
        return self.__parentValue

    # The value passed to this function in v should be the value that was given
    # to the key that we are dependent on.  This function will set self.control
    # to the proper one from our list of controls.
    @parentValue.setter
    def parentValue(self, v):
        if self.dependent:
            for d in self.definitions:
                # check if the compare value is a list and iterate through it.
                if isinstance(d.compare, list):
                    for each in d.compare:
                        if each == v:
                            self.control = d
                # or just check the new value against the comparison value
                else:
                    if d.compare == v:
                        # TODO: also add some ability to use expressions like > or <
                        self.control = d
        self.__parentValue = v

    @property
    def value(self):
        return self.__value
    
    @value.setter
    def value(self, v):
        self.__value = v
        if self.dependentChildren:
            for each in self.dependentChildren:
                each.parentValue = v

    @property
    def name(self):
        if self.control:
            return self.control.name
        else:
            return "-"

    @name.setter
    def name(self, m):
        if self.control:
            self.control.name = m

    @property
    def units(self):
        if self.control:
            return self.control.units
        else:
            return ""

    @units.setter
    def units(self, m):
        if self.control:
            self.control.units = m

    @property
    def multiplier(self):
        if self.control:
            return self.control.multiplier
        else:
            return None

    @multiplier.setter
    def multiplier(self, m):
        if self.control:
            self.control.multiplier = m

    @property
    def input(self):
        if self.control:
            return self.control.input
        else:
            return None

    @input.setter
    def input(self, m):
        if self.control:
            self.control.input = m

    @property
    def datatype(self):
        if self.control:
            return self.control.datatype
        else:
            return None

    @datatype.setter
    def datatype(self, m):
        if self.control:
            self.control.datatype = m
    

    # return a ttk widget that can be used to edit this key/value pair
    def widget(self, parent):
        input = self.input.lower()
        if input == "entry":
            if self.datatype.upper() in configNode.int_types:
                self.__widget = IntEntry(parent)
            elif self.datatype.upper() == "FLOAT":
                self.__widget = FloatEntry(parent)
            elif self.datatype.upper() == "CHAR":
                self.__widget = TextEntry(parent)
        elif input == "list":
                self.__widget = ListBox(parent, self.control.selections)

        return self.__widget




class ConfigTree(ttk.Treeview):
    def __init__(self, parent, node, *args, **kwargs):
        ttk.Treeview.__init__(self, parent, *args, columns=('key', 'description', 'value', 'units'), selectmode='browse', show='headings', **kwargs)
        self.node = node
        self['columns'] = ('key', 'description', 'value', 'units')
        self.column('key', width=40, stretch=False)
        self.heading('key', text='Key')
        self.column('description', stretch=True)
        self.heading('description', text='Description')
        self.column('value', width=40,  stretch=False)
        self.heading('value', text='Value')
        self.column('units', width=40,  stretch=False)
        self.heading('units', text='Units')
        self.records = []
        self.tag_configure('dirty', foreground='#FF0000')

        for c in node.device.configuration:
            self.records.append(ConfigRecord(c))

        # This loops through all the configuration items and sets references for the
        # dependent keys so that we can analyze them later.
        for i in self.records:
            if i.dependent:
                for each in self.records:
                    if each.key == i.parentKey:
                        each.dependentChildren.append(i)

        for i in self.records:
            cfg = configNode.queryNodeConfiguration(config.node, node.nodeid, i.key)
            try:
                cfg.datatype = i.datatype
                cfg.multiplier = i.multiplier
                i.value = cfg.value
                if i.dependentChildren:
                    for each in i.dependentChildren:
                        each.parentValue = i.value

                self.insert('', 'end', iid=i.key, values = [i.key, i.name, i.value, i.units])
            except:
                self.insert('', 'end', iid=i.key, values = [i.key, "-", "-", ""])
    
    # TODO only set the dirty flag and tags when the value is different than what we read from the node
    def set_value(self, recordKey, value):
        self.set(recordKey, "value", value)
        self.item(recordKey, tags="dirty")
        for i in self.records:
            if i.key == recordKey:
                i.dirty = True
                i.value = value


        
         




# Dialog box used to get information from the user regarding the
# python-can connection that we wish to make.
class ConfigDialog(tk.Toplevel):
    def __init__(self, parent, node, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)

        self.title("CANFiX Configuration Utility - Config")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        mainFrame = ttk.Frame(self) # main form where we put the interface and dynamic widgets
        mainFrame.grid(column=0,row=0,sticky=tk.NSEW, padx=2, pady=2)
        mainFrame.grid_rowconfigure(0, weight=1)
        mainFrame.grid_columnconfigure(0, weight=1)

        self.treeView = ConfigTree(mainFrame, node)
        self.treeView.grid(column=0, row=0, sticky=tk.NSEW)
        self.treeView.bind("<<TreeviewSelect>>", self.configSelect)

        sb = ttk.Scrollbar(mainFrame, command=self.treeView.yview)
        sb.grid(column=1, row=0, sticky=tk.NS)
        self.treeView.configure(yscrollcommand=sb.set)

        self.cfgFrame = ttk.Frame(self, height=60) # Frame for the configuration.
        self.cfgFrame.grid(column=0, row=1, sticky=tk.NSEW)
        self.cfgFrame.grid_columnconfigure(0, weight=1)

        self.cfgLabel = ttk.Label(self.cfgFrame, text = "-")
        self.cfgLabel.grid(column=0, row=0, padx=4, pady=4, sticky=tk.W)

        self.cfgBtn = ttk.Button(self.cfgFrame, text="Apply", command=self.cfg_apply)
        self.cfgBtn.grid(column=1, row=0, padx=4, pady=4, sticky=tk.E)

        btnFrame = ttk.Frame(self) # Frame for the buttons.
        btnFrame.grid(column=0, row=2, sticky=tk.E)

        # cancel and ok buttons
        btnCancel = ttk.Button(btnFrame, text="Close", command=self.close_mod)
        btnCancel.grid(row=0, column=0, sticky=tk.SE, padx=4, pady=4)
        btnOk = ttk.Button(btnFrame, text="Send", command=self.btn_send)
        btnOk.grid(row=0, column=1, sticky=tk.SE, padx=4, pady=4)

        self.protocol("WM_DELETE_WINDOW", self.close_mod)
        self.grab_set() # makes the dialog modal


    def configSelect(self, e):
        curItem = self.treeView.focus()
        item = self.treeView.item(curItem)
        self.cfgLabel["text"] = item["values"][1]

        widgets = self.cfgFrame.winfo_children()
        # remove and delete all the controls except the label and the button
        for i in widgets:
            if i is not self.cfgLabel and i is not self.cfgBtn:
                i.grid_remove()
                i.destroy()
        # find the item that we clicked on
        for each in self.treeView.records:
            if each.key == item["values"][0]:
                self.cfgWidget = each.widget(self.cfgFrame)
                self.cfgWidget.grid(row=1,column=0, sticky=tk.E)
                if each.units:
                    l = ttk.Label(self.cfgFrame, text = each.units)
                    l.grid(row=1, column=1, padx = 4, sticky=tk.W)
                self.currentItem = each
                

    def cfg_apply(self):
        self.treeView.set_value(self.currentItem.key, self.cfgWidget.value)

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
