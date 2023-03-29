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
from .connectTk  import ConnectDialog
import tkinter as tk
import tkinter.ttk as ttk
import queue

log = logging.getLogger(__name__)

# Command Queue commands
ADD_NODE = 1
DEL_NODE = 2
UPDATE_NODE = 3
ADD_PARAMETER = 4
DEL_PARAMETER = 5
UPDATE_PARAMETER = 6

class StatusBar(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.variable=tk.StringVar()
        self.label=tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                           textvariable=self.variable,
                           font=('arial',10,'normal'))
        self.variable.set('')
        self.label.pack(fill=tk.X)

    def set(self, value):
        self.variable.set(str(value))

class cfTab(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

class NodeView(ttk.Treeview):
    def __init__(self, master):
        columns = ('id', 'name', 'data')

        ttk.Treeview.__init__(self, master, columns = columns, selectmode='browse')
        self.heading('#0', text="")
        self.column('#0', width=20, stretch=False)
        self.heading('id', text="ID")
        self.column('id', width=40, stretch=False)
        self.heading('name', text="Name")
        self.column('name', stretch=True)
        self.heading('data', text="Data")
        self.column('data', stretch=True)

class ParameterView(ttk.Treeview):
    def __init__(self, master):
        columns = ('node', 'pid', 'name', 'value', 'quality')

        ttk.Treeview.__init__(self, master, columns = columns, selectmode='browse', show='headings')
        self.heading('node', text="Node")
        self.column('node', width=40, stretch=False)
        self.heading('pid', text="PID")
        self.column('pid', width=50, stretch=False)
        self.heading('name', text="Name")
        self.column('name', stretch=True)
        self.heading('value', text="Value")
        self.column('value', stretch=True)
        self.heading('quality', text="Quality")
        self.column('quality', width=80, stretch=False)


class App(tk.Tk):
    def __init__(self, parent, *args, **kwargs):
        tk.Tk.__init__(self, parent, *args, **kwargs)
        self.title("CANFiX Configuration Utility")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.nb = ttk.Notebook(self)
        self.cmd_queue = queue.Queue()

        self.nt = nodes.NodeThread()
        self.nt.set_node_callbacks(self.add_node, self.del_node, self.update_node)
        self.nt.set_parameter_callbacks(self.add_parameter, self.del_parameter, self.update_parameter)
        connection.canbus.connectedCallback = self.connect_callback
        connection.canbus.disconnectedCallback = self.disconnect_callback

        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        file_menu = tk.Menu(self.menubar, tearoff = 0)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.destroy, underline=1)
        self.node_menu = tk.Menu(self.menubar, tearoff = 0)
        self.node_menu.add_command(label='Connect...', underline=0, command=self.connect)
        self.node_menu.add_command(label='Disconnect...', underline=0, command=self.disconnect)
        self.node_menu.add_separator()
        self.node_menu.add_command(label='Information...', underline=0, command=self.show_information)
        self.node_menu.add_command(label='Configure Node...', underline=1, command=self.configure_node)
        self.node_menu.add_separator()
        self.node_menu.add_command(label='Update Firmware...', underline=0)
        if connection.canbus.connected:
            self.node_menu.entryconfig('Connect...', state='disabled')
        else:
            self.node_menu.entryconfig('Disconnect...', state='disabled')
        help_menu = tk.Menu(self.menubar, tearoff = 0)
        help_menu.add_command(label='Specification', underline=0)
        help_menu.add_separator()
        help_menu.add_command(label='About', underline=0)
        self.menubar.add_cascade(label="File", menu=file_menu, underline=0)
        self.menubar.add_cascade(label="Node", menu=self.node_menu, underline=0)
        self.menubar.add_cascade(label="Help", menu=help_menu, underline=0)

        nodeTab = cfTab(self.nb)
        parameterTab = cfTab(self.nb)
        dataTab = cfTab(self.nb)

        self.nb.add(nodeTab, text="Nodes")
        self.nb.add(parameterTab, text="Parameters")
        self.nb.add(dataTab, text="Data")

        self.nodeview = NodeView(nodeTab)
        self.parameterView = ParameterView(parameterTab)

        self.nodeview.grid(row=0, column=0, sticky=tk.NSEW)
        nodescroll = ttk.Scrollbar(nodeTab, orient=tk.VERTICAL, command=self.nodeview.yview)
        self.nodeview.configure(yscroll=nodescroll.set)
        nodescroll.grid(row=0, column=1, sticky='ns')

        self.parameterView.grid(row=0, column=0, sticky=tk.NSEW)
        paramscroll = ttk.Scrollbar(parameterTab, orient=tk.VERTICAL, command=self.parameterView.yview)
        self.parameterView.configure(yscroll=paramscroll.set)
        paramscroll.grid(row=0, column=1, sticky='ns')
        self.nb.pack(expand=True, fill=tk.BOTH, side=tk.TOP)
        self.sb = StatusBar(self)
        if connection.canbus.connected:
            self.sb.set("Connected")
        else:
            self.sb.set("Not Connected")

        self.sb.pack(fill=tk.X)

        # nodeTab.bind("<Visibility>", self.node_show)
        # parameterTab.bind("<Visibility>", self.parameter_show)
        self.nodeview.bind("<Double-Button-1>", self.node_select)
        self.parameterView.bind("<Double-Button-1>", self.parameter_select)

    # These are callbacks that would be called from the node thread.  Commands
    # are added to the queue so that the gui thread can make updates.
    def add_node(self, node):
        self.cmd_queue.put((ADD_NODE, node))

    def del_node(self, node):
        self.cmd_queue.put((DEL_NODE, node))

    def update_node(self, node):
        self.cmd_queue.put((UPDATE_NODE, node))

    def add_parameter(self, parameter):
        self.cmd_queue.put((ADD_PARAMETER, parameter))

    def del_parameter(self, parameter):
        self.cmd_queue.put((DEL_PARAMETER, parameter))

    def update_parameter(self, parameter):
        self.cmd_queue.put((UPDATE_PARAMETER, parameter))

    def connect_callback(self):
        self.node_menu.entryconfig('Connect...', state='disabled')
        self.node_menu.entryconfig('Disconnect...', state='normal')

    def disconnect_callback(self):
        self.node_menu.entryconfig('Connect...', state='normal')
        self.node_menu.entryconfig('Disconnect...', state='disabled')

    def __get_current_node(self):
        curItem = self.nodeview.focus()
        parent = self.nodeview.parent(curItem)
        item = self.nodeview.item(curItem)
        if parent != "":
            node = parent
        else:
            if item['values']:
                node = item['values'][0]
            else:
                node = None
        return node

    def __get_current_parameter(self):
        curItem = self.parameterView.focus()
        item = self.parameterView.item(curItem)
        return item

    def show_information(self):
        tab = self.nb.tab('current')
        if tab['text'] == "Nodes":
            node = self.__get_current_node()
            if node is not None:
                print("Information Node {}".format(node))
            else:
                print("No Node Selected")
        elif tab['text'] == "Parameters":
            item = self.__get_current_parameter()
            if item['values']:
                p = item['values'][1]
                print("Information for {}".format(p))
            else:
                print("No Parameter Selected")
        else:
            pass

    # Main GUI functions
    def connect(self):
        cd = ConnectDialog(self)
        cd.mainloop()

        if cd.okay:
            try:
                self.sb.set("Connecting")
                args = cd.arguments
                connection.canbus.connect(cd.interface, **args)
                self.sb.set("Connected")
            except Exception as e:
                log.error(e)
                self.sb.set(e)
        cd.destroy()

    def disconnect(self):
        self.sb.set("Disconnecting")
        connection.canbus.disconnect()
        self.sb.set("Disconnected")


    def configure_node(self):
        tab = self.nb.tab('current')
        node = None
        if tab['text'] == "Nodes":
            node = self.__get_current_node()
        elif tab['text'] == "Parameters":
            item = self.__get_current_parameter()
            if item['values']:
                node = item['values'][0]
        if node is not None:
            print("Configure Node {}".format(node))
        else:
            print("No Node Selected")

    def node_select(self, event):
        self.show_information()

    def parameter_select(self, event):
        self.show_information()


    def manager(self):
        done = False
        while(not done):
            try:
                cmd = self.cmd_queue.get(block=False)
            except queue.Empty:
                done = True
            except Exception as e:
                print(e)
            else:
                try: #TODO This is a bit heavy handed but it keeps the GUI working when weird stuff happens
                    if cmd[0] == ADD_NODE:
                        self.nodeview.insert('', tk.END, values=(cmd[1].nodeid, cmd[1].name, ''), iid=cmd[1].nodeid, open=False)
                        self.nodeview.insert(cmd[1].nodeid, tk.END, values = ('', 'Device', cmd[1].deviceid), iid=str(cmd[1].nodeid)+".device", open=False)
                        self.nodeview.insert(cmd[1].nodeid, tk.END, values = ('', 'Model', cmd[1].model), iid=str(cmd[1].nodeid)+".model", open=False)
                        self.nodeview.insert(cmd[1].nodeid, tk.END, values = ('', 'Version', cmd[1].version), iid=str(cmd[1].nodeid)+".version", open=False)
                    elif cmd[0] == UPDATE_NODE:
                        self.nodeview.set(cmd[1].nodeid, 'name', cmd[1].name)
                        self.nodeview.set(str(cmd[1].nodeid)+".device", 'data', cmd[1].deviceid)
                        self.nodeview.set(str(cmd[1].nodeid)+".model", 'data', cmd[1].model)
                        self.nodeview.set(str(cmd[1].nodeid)+".version", 'data', cmd[1].version)
                    elif cmd[0] == DEL_NODE:
                        self.nodeview.delete(cmd[1].nodeid)
                    elif cmd[0] == ADD_PARAMETER:
                        if cmd[1].indexName is not None:
                            pid = "{}.{}".format(cmd[1].pid, cmd[1].index)
                        else:
                            pid = str(cmd[1].pid)
                        v = (cmd[1].nodeid,
                            pid,
                            cmd[1].name,
                            "{} {}".format(cmd[1].value, cmd[1].units),
                            cmd[1].quality)
                        self.parameterView.insert('', tk.END, values=v, iid=(cmd[1].pid, cmd[1].index), open=False)
                    elif cmd[0] == DEL_PARAMETER:
                        self.parameterView.delete((cmd[1].pid, cmd[1].index))
                    elif cmd[0] == UPDATE_PARAMETER:
                        self.parameterView.set((cmd[1].pid, cmd[1].index), 'value', "{} {}".format(cmd[1].value, cmd[1].units))
                        self.parameterView.set((cmd[1].pid, cmd[1].index), 'quality', cmd[1].quality)
                except Exception as e:
                    print(e) #TODO change to debug logging


        self.after(1000, self.manager)

    def run(self):
        self.nt.start() # Start the Node Handling Thread
        self.after(1000, self.manager)
        self.mainloop() # Start the GUI
        self.nt.stop()


if __name__ == "__main__":
    app = App()
    app.run()
