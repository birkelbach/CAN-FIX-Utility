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
from . import configNode
import tkinter as tk
import tkinter.ttk as ttk
import canfix

log = logging.getLogger(__name__)

class ConfigError(Exception):
    pass


# These are the custom widgets that we use for editing the configuration.  They
# are smart enough to deal with the types and min/max attributes of the key.
# Each should generate an <<Update>> event when the widget thinks the list
# should change.  Each should expose a .value property that will deal with
# converting the display in the widget to what is appropriate for sending
# over the network as the configuration value.
class TextEntry(tk.Entry):
    def __init__(self, parent, *args, **kwargs):
        tk.Entry.__init__(self, parent, *args, **kwargs)
        self.bind("<FocusOut>", self.update_event)

    def update_event(self, e):
        self.event_generate("<<Update>>" )

    @property
    def value(self):
        return self.get()


class IntEntry(tk.Entry):
    def __init__(self, parent, *args, **kwargs):
        self.text = tk.StringVar()
        tk.Entry.__init__(self, parent, textvariable=self.text, *args, **kwargs)
        self.bind("<FocusOut>", self.update_event)

    def update_event(self, e):
        self.event_generate("<<Update>>" )

    @property
    def value(self):
        return int(self.text.get())

    @value.setter
    def value(self, v):
        if v is None: v = 0
        self.text.set(str(int(v)))


class FloatEntry(tk.Entry):
    def __init__(self, parent, *args, **kwargs):
        self.text = tk.StringVar()
        tk.Entry.__init__(self, parent, textvariable=self.text, *args, **kwargs)
        self.bind("<FocusOut>", self.update_event)

    def update_event(self, e):
        self.event_generate("<<Update>>" )

    @property
    def value(self):
        return float(self.get())

    @value.setter
    def value(self, v):
        self.text.set(str(float(v)))


class ListBox(ttk.Combobox):
    def __init__(self, parent, selections, *args, **kwargs):
        ttk.Combobox.__init__(self, parent, *args, **kwargs)
        self.selections = selections
        self["values"] = list(self.selections.keys())
        self.bind("<<ComboboxSelected>>", self.update_event)

    def update_event(self, e):
        self.event_generate("<<Update>>" )

    @property
    def value(self):
        return self.selections[self.get()]

    @value.setter
    def value(self, v):
        for key, value in self.selections.items():
            if value == v:
                self.set(key)
        # If we don't have a match then ignore it.


class BitSelectBox(tk.Frame):
    def __init__(self, parent, selections, bitsize, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.selections = selections
        self.variables = []*bitsize
        for x in range(bitsize):
            self.variables.append(tk.IntVar(self, 0))
        self.checks = []
        x = 0
        for k, v in selections.items():
            cb = ttk.Checkbutton(self, text = k, variable=self.variables[v], onvalue=1, offvalue=0, command=self.update_event)
            cb.grid(column=0, row=x, sticky=tk.W)
            self.checks.append(cb)
            x += 1

    def update_event(self):
        self.event_generate("<<Update>>" )

    @property
    def value(self):
        v=0
        for i, x in enumerate(self.variables):
            v += 2**i * x.get()

        return v

    @value.setter
    def value(self, v):
        if isinstance(v, list): # BYTEs and WORDs are returned as lists of BOOLS from che canfix module
            for x in range(len(self.variables)):
                if v[x]:
                    self.variables[x].set(1)
                else:
                    self.variables[x].set(0)
        else: # treat it like an integer
            for x in range(len(self.variables)):
                if v & 2**x:
                    self.variables[x].set(1)
                else:
                    self.variables[x].set(0)
        # If it's neither then let the exceptions rise, we've messed up somewhere



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
            self.datatype = item["type"].upper()
        else:
            self.datatype = "UINT" #default to 16 bit unsigned ?????
        if "input" in item:
            self.input = item["input"]
        else:
            self.input = "entry"
        if "min" in item:
            if self.datatype == "FLOAT":
                self.min = float(item["min"])
            else:
                self.min = int(item["min"])
        else:
            self.min = None
        if "max" in item:
            if self.datatype == "FLOAT":
                self.max = float(item["max"])
            else:
                self.max = int(item["max"])
        else:
            self.max = None
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
        self.__parentValue = None
        self.dependentChildren = []
        self.__value = None
        self.__saved_value = self.__value
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
        if isinstance(v, list):
            x = 0
            for i, val in enumerate(v):
                if val: x += 2**i
            self.__value = x
        else:
            if self.min != None and v < self.min:
                self.__value = self.min
            elif self.max != None and v > self.max:
                self.__value = self.max
            else:
                self.__value = v
        if self.dependentChildren:
            for each in self.dependentChildren:
                each.parentValue = v

    @property
    def value_text(self):
        if self.value == None:
            return "-" # If we get here then we didn't match anything but we need to do this.
        elif self.input == 'list':
            for key, value in self.control.selections.items():
                if value == self.value:
                    return key
            return "-" # If we don't find it in the list
        elif self.input == 'entry':
            if self.datatype in configNode.int_types:
                return str(int(self.value))
            elif self.datatype == "FLOAT":
                return "{:.2f}".format(self.value)
            elif self.datatype in [ "BYTE", "WORD" ]:
                return "0x{:x}".format(self.value)
        elif self.input == 'select':
            if self.datatype == "BYTE":
                return "{:08b}".format(self.value)
            elif self.datatype == "WORD":
                return "{:016b}".format(self.value)
            else:
                raise ValueError("select input must be BYTE or WORD")


    @property
    def dirty(self):
        return self.__value != self.__saved_value

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
    def min(self):
        if self.control:
            return self.control.min
        else:
            return None

    @min.setter
    def min(self, m):
        if self.control:
            self.control.min = m

    @property
    def max(self):
        if self.control:
            return self.control.max
        else:
            return None

    @max.setter
    def max(self, m):
        if self.control:
            self.control.max = m

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
            self.control.input = m.lower()

    @property
    def datatype(self):
        if self.control:
            return self.control.datatype
        else:
            return None

    @datatype.setter
    def datatype(self, m):
        if self.control:
            self.control.datatype = m.upper()

    def save(self):
        self.__saved_value = self.value

    # return a ttk widget that can be used to edit this key/value pair
    def widget(self, parent):
        input = self.input.lower()
        if input == "entry":
            if self.datatype.upper() in (configNode.int_types + ["BYTE", "WORD"]):
                self.__widget = IntEntry(parent)
            elif self.datatype.upper() == "FLOAT":
                self.__widget = FloatEntry(parent)
            elif self.datatype.upper() == "CHAR":
                self.__widget = TextEntry(parent)
        elif input == "list":
            self.__widget = ListBox(parent, self.control.selections)
        elif input == "select":
            if self.datatype =="BYTE":
                self.__widget = BitSelectBox(parent, self.control.selections, 8)
            elif self.datatype =="WORD":
                self.__widget = BitSelectBox(parent, self.control.selections, 16)
            else:
                raise ConfigError("select input type should be for BYTE or WORD only")
        else:
            raise ConfigError("Unknown input type")

        self.__widget.value = self.value
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
        self.column('value', width=100,  stretch=True)
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
            try:
                i.value = self.get_config_value(i)
                i.save()
                if i.dependentChildren:
                    for each in i.dependentChildren:
                        each.parentValue = i.value

                self.insert('', 'end', iid=i.key, values = [i.key, i.name, i.value_text, i.units])
            except Exception as e:
                #print(e)
                self.insert('', 'end', iid=i.key, values = [i.key, i.name, "-", ""])
                #raise(e)


    def set_config_value(self, record):
        cfg = configNode.setNodeConfiguration(config.node, self.node.nodeid, record.key, record.datatype, record.multiplier, record.value)
        if cfg.status == canfix.MSG_FAIL:
            log.error("Unable to set configuration for key {}, error code = {}".format(record.key, cfg.errorCode))


    def get_config_value(self, record):
        try:
            cfg = configNode.queryNodeConfiguration(config.node, self.node.nodeid, record.key)
            if cfg != None:
                cfg.datatype = record.datatype
                cfg.multiplier = record.multiplier
                record.save()  # It's not dirty anymore
                return cfg.value
            else:
                return None
        except:
            return None

    # This reads all the record values from the node and updates the list
    def refresh(self):
        for i in self.records:
            i.value = self.get_config_value(i)
            self.set_value(i.key, i.value)

    def send_config(self):
        # Loop through all the records and send the dirty ones.
        for i in self.records:
            if i.dirty:
                self.set_config_value(i)
        # We need to refresh the list after writing because the node may change some
        # configurations based on data that we send.  There may also be command words
        # that get reset, etc.
        self.refresh()


    # Sets a value in the tree.  Makes sure that any dependent keys are changed if
    # necessary.
    def set_value(self, recordKey, value):
        for i in self.records:
            if i.key == recordKey:
                record = i
        #i.dirty = True
        record.value = value
        self.set(recordKey, "value", record.value_text)
        if record.dirty:
            self.item(recordKey, tags="dirty")
        else:
            self.item(recordKey, tags="")
        # if we have dependent children then we also need to update these
        if record.dependentChildren:
            for d in record.dependentChildren:
                self.set(d.key, "description", d.name)
                self.set(d.key, "value", d.value_text)
                self.set(d.key, "units", d.units)
                if d.dirty:
                    self.item(d.key, tags="dirty")
                else:
                    self.item(d.key, tags="")



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
        id = self.treeView.get_children()[0]
        self.treeView.focus(id)
        self.treeView.selection_set(id)

        sb = ttk.Scrollbar(mainFrame, command=self.treeView.yview)
        sb.grid(column=1, row=0, sticky=tk.NS)
        self.treeView.configure(yscrollcommand=sb.set)

        self.cfgFrame = ttk.Frame(self, height=60) # Frame for the configuration.
        self.cfgFrame.grid(column=0, row=1, sticky=tk.NSEW)
        self.cfgFrame.grid_columnconfigure(0, weight=1)

        self.cfgLabel = ttk.Label(self.cfgFrame, text = "-")
        self.cfgLabel.grid(column=0, row=0, padx=4, pady=4, sticky=tk.W)

        btnFrame = ttk.Frame(self) # Frame for the buttons.
        btnFrame.grid(column=0, row=2, sticky=tk.E)

        # cancel and ok buttons
        btnCancel = ttk.Button(btnFrame, text="Close", command=self.close_mod, takefocus=0)
        btnCancel.grid(row=0, column=0, sticky=tk.SE, padx=4, pady=4)
        btnSend = ttk.Button(btnFrame, text="Send", command=self.btn_send, underline=0, takefocus=0)
        btnSend.grid(row=0, column=1, sticky=tk.SE, padx=4, pady=4)

        self.bind("<Control-s>", self.btn_send)
        self.bind("<Escape>", self.close_mod)

        self.protocol("WM_DELETE_WINDOW", self.close_mod)
        self.grab_set() # makes the dialog modal


    # event called when the users changes which item is selected in the tree
    def configSelect(self, e):
        curItem = self.treeView.focus()
        item = self.treeView.item(curItem)
        self.cfgLabel["text"] = item["values"][1]

        widgets = self.cfgFrame.winfo_children()
        # remove and delete all the controls except the label and the button
        for i in widgets:
            if i is not self.cfgLabel:
                i.grid_remove()
                i.destroy()
        # find the item that we clicked on
        for each in self.treeView.records:
            if each.key == item["values"][0]:
                self.cfgWidget = each.widget(self.cfgFrame)
                self.cfgWidget.grid(row=1,column=0, padx=4,sticky=tk.EW)
                self.cfgWidget.bind("<<Update>>", self.cfg_apply)
                if each.units:
                    l = ttk.Label(self.cfgFrame, text = each.units)
                    l.grid(row=1, column=1, padx = 4, sticky=tk.W)
                self.currentItem = each


    def cfg_apply(self, e):
        # TODO deal with the exceptions for values that can't be converted properly
        self.treeView.set_value(self.currentItem.key, self.cfgWidget.value)

    # send button callback.
    def btn_send(self, e=None):
        self.treeView.send_config()

    def close_mod(self, e=None):
        # top right corner cross click: return value ;`x`;
        # we need to send it a value, otherwise there will be an exception when closing parent window
        self.returning = ";`x`;"
        self.quit()

if __name__ == "__main__":
    pass

