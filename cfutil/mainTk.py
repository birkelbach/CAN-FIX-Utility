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

# TODO Get rid of the .pack() geometry managers and stick with .grid()

import logging
import logging.config
from threading import Thread
import canfix
from . import nodes
from . import connection
from . import settings
from .connectTk  import ConnectDialog
from .configTk  import ConfigDialog
from .infoTk import InfoDialog
from .paramInfoTk import ParamInfoDialog
from .firmwareTk import FirmwareDialog
from .loadsaveTk import LoadDialog, SaveDialog
from .prefsTk import PrefsDialog
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import tkinter.ttk as ttk
from tkinter.messagebox import showerror
import queue

log = logging.getLogger(__name__)

# Command Queue commands
ADD_NODE = 1
DEL_NODE = 2
UPDATE_NODE = 3
ADD_PARAMETER = 4
DEL_PARAMETER = 5
UPDATE_PARAMETER = 6
TRAFFIC_MESSAGE = 7

class TrafficThread(Thread):
    def __init__(self, callback):
        Thread.__init__(self)
        self.getout = False
        self.msg_callback = callback

    def run(self):
        self.conn = connection.canbus.get_connection()
        while(not self.getout):
            try:
                msg = self.conn.recv(0.5)
                self.msg_callback(msg)
            except connection.Timeout:
                pass
            except Exception as e:
                log.error(e)
        connection.canbus.free_connection(self.conn)

    def stop(self):
        self.getout = True

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
        g = settings.get("main_geometry")
        if g:
            self.geometry(g)

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
        file_menu.add_command(label='Save Configuration...', command=self.save_configuration, underline=0)
        file_menu.add_command(label='Load Configuration...', command=self.load_configuration, underline=0)
        file_menu.add_separator()
        file_menu.add_command(label='Preferences...', command=self.preferences, underline=0)
        file_menu.entryconfig('Preferences...', state='disabled') # Temporary until we finish the preferences
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.destroy, underline=1)

        self.comm_menu = tk.Menu(self.menubar, tearoff = 0)
        self.comm_menu.add_command(label='Connect...', underline=0, command=self.connect)
        self.comm_menu.add_command(label='Disconnect...', underline=0, command=self.disconnect)
        if connection.canbus.connected:
            self.comm_menu.entryconfig('Connect...', state='disabled')
        else:
            self.comm_menu.entryconfig('Disconnect...', state='disabled')

        self.tools_menu = tk.Menu(self.menubar, tearoff = 0)
        self.tools_menu.add_command(label='Information...', underline=0, command=self.show_information)
        #self.tools_menu.add_separator()
        self.tools_menu.add_command(label='Configure Node...', underline=1, command=self.configure_node)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label='Update Firmware...', underline=0, command=self.load_firmware)
        help_menu = tk.Menu(self.menubar, tearoff = 0)
        help_menu.add_command(label='Specification', underline=0)
        help_menu.add_separator()
        help_menu.add_command(label='About', underline=0)

        self.menubar.add_cascade(label="File", menu=file_menu, underline=0)
        self.menubar.add_cascade(label="Comms", menu=self.comm_menu, underline=0)
        self.menubar.add_cascade(label="Tools", menu=self.tools_menu, underline=0)
        self.menubar.add_cascade(label="Help", menu=help_menu, underline=0)

        nodeTab = cfTab(self.nb)
        parameterTab = cfTab(self.nb)
        trafficTab = cfTab(self.nb)

        self.nb.add(nodeTab, text="Nodes")
        self.nb.add(parameterTab, text="Parameters")
        self.nb.add(trafficTab, text="Traffic")

        self.nodeview = NodeView(nodeTab)
        self.parameterView = ParameterView(parameterTab)

        # Node Tab
        self.nodeview.grid(row=0, column=0, sticky=tk.NSEW)
        nodescroll = ttk.Scrollbar(nodeTab, orient=tk.VERTICAL, command=self.nodeview.yview)
        self.nodeview.configure(yscroll=nodescroll.set)
        nodescroll.grid(row=0, column=1, sticky='ns')

        # Parameter Tab
        self.parameterView.grid(row=0, column=0, sticky=tk.NSEW)
        paramscroll = ttk.Scrollbar(parameterTab, orient=tk.VERTICAL, command=self.parameterView.yview)
        self.parameterView.configure(yscroll=paramscroll.set)
        paramscroll.grid(row=0, column=1, sticky='ns')

        # Traffic Tab
        self.trafficbox = ScrolledText(trafficTab)
        self.trafficbox.grid(row=0, column=0, padx=2, pady=2, sticky=tk.NSEW, columnspan=2)
        self.trafficRawVar = tk.IntVar()
        trafficRawCheck = ttk.Checkbutton(trafficTab, text="Raw CAN Messages", variable=self.trafficRawVar)
        trafficRawCheck.grid(row=1, column=0, padx=4, pady=4, sticky=tk.E, columnspan=2)
        self.clearnButton = ttk.Button(trafficTab, text = "Clear", command=self.clear_traffic)
        self.clearnButton.grid(row=2, column=0, padx=4, pady=4, sticky=tk.E)
        self.trafficButton = ttk.Button(trafficTab, text = "Start", command=self.start_traffic)
        self.trafficButton.grid(row=2, column=1, padx=4, pady=4, sticky=tk.E)

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
        self.protocol("WM_DELETE_WINDOW", self.close_mod)

    def close_mod(self):
        settings.set("main_geometry", self.geometry())
        self.destroy()


    # These are callbacks that would be called from the node thread.  Commands
    # are added to the queue so that the gui thread can make updates.
    # TODO Change these to use the custom virtual events instead of the command queue
    #      This doesn't really work because there is no good way to pass data with the event
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

    # This function is called from the TrafficThread to put the
    # messages on the cmd_queue for the traffic tab
    def traffic_callback(self, msg):
        self.cmd_queue.put((TRAFFIC_MESSAGE, msg))

    def start_traffic(self): # Start Traffic button
        self.trafficThread = TrafficThread(self.traffic_callback)
        self.trafficThread.start()
        self.trafficButton.configure(command = self.stop_traffic, text = "Stop")

    def stop_traffic(self): # Stop Traffic button
        self.trafficThread.stop()
        self.trafficThread.join(1.0)
        self.trafficThread = None
        self.trafficButton.configure(command = self.start_traffic, text = "Start")

    def clear_traffic(self): # Clear Traffic button
        self.trafficbox['state']='normal'
        self.trafficbox.delete('1.0', tk.END)
        self.trafficbox['state']='disabled'

    def connect_callback(self):
        self.comm_menu.entryconfig('Connect...', state='disabled')
        self.comm_menu.entryconfig('Disconnect...', state='normal')

    def disconnect_callback(self):
        self.comm_menu.entryconfig('Connect...', state='normal')
        self.comm_menu.entryconfig('Disconnect...', state='disabled')

    def __get_current_node(self):
        curItem = self.nodeview.focus()
        parent = self.nodeview.parent(curItem)
        item = self.nodeview.item(curItem)
        if parent != "":
            node = int(parent)
            print(node)
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
                id = InfoDialog(self, self.nt.nodelist[node])
                id.mainloop()
                id.destroy()
            else:
                showerror("Error", message="No Node Selected")
                # TODO Error Pop Up
        elif tab['text'] == "Parameters":
            item = self.__get_current_parameter()
            if item['values']:
                p = item['values'][1]
                id = ParamInfoDialog(self, p, self.nt)
                id.mainloop()
                id.destroy()
            else:
                showerror("Error", message="No Parameter Selected")
        else:
            pass

    # Main GUI functions
    def load_configuration(self):
        node = self.__get_current_node()
        if node is not None:
            ld = LoadDialog(self, self.nt.nodelist, node)
        else:
            ld = LoadDialog(self, self.nt.nodelist, None)
        ld.mainloop()
        ld.destroy()


    def save_configuration(self):
        node = self.__get_current_node()
        if node is not None:
            sd = SaveDialog(self, self.nt.nodelist, node)
        else:
            sd = SaveDialog(self, self.nt.nodelist, None)
        sd.mainloop()
        sd.destroy()

    def preferences(self):
        prefs = PrefsDialog(self)
        prefs.mainloop()
        prefs.destroy()


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
        self.update_idletasks()
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
            try:
                cd = ConfigDialog(self, self.nt.nodelist[node])
            except Exception as e:
                self.sb.set(f"Error: {e}")
                return
            cd.mainloop()
            cd.destroy()
        else:
            showerror("Error", message="No Node Selected")

    def load_firmware(self):
        tab = self.nb.tab('current')
        node = None
        if tab['text'] == "Nodes":
            node = self.__get_current_node()
        elif tab['text'] == "Parameters":
            item = self.__get_current_parameter()
            if item['values']:
                node = item['values'][0]

        fd = FirmwareDialog(self, self.nt.nodelist, node)
        fd.mainloop()
        fd.destroy()


    def node_select(self, event):
        pass
        #self.show_information()

    def parameter_select(self, event):
        pass
        #self.show_information()

    # TODO instead of all this queue crap we need to use custom virtual events.
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
                            cmd[1].valstring,
                            cmd[1].quality)
                        self.parameterView.insert('', tk.END, values=v, iid=(cmd[1].pid, cmd[1].index), open=False)
                    elif cmd[0] == DEL_PARAMETER:
                        self.parameterView.delete((cmd[1].pid, cmd[1].index))
                    elif cmd[0] == UPDATE_PARAMETER:
                        self.parameterView.set((cmd[1].pid, cmd[1].index), 'value', cmd[1].valstring)
                        self.parameterView.set((cmd[1].pid, cmd[1].index), 'quality', cmd[1].quality)
                    elif cmd[0] == TRAFFIC_MESSAGE:
                        if self.trafficRawVar.get():
                            s = f"{str(cmd[1])}\n"
                        else:
                            p = canfix.parseMessage(cmd[1])
                            s = f"{str(p)}\n"
                        self.trafficbox['state']='normal'
                        noscroll = self.trafficbox.yview()
                        self.trafficbox.insert(tk.END, s)
                        # this let's the user move the scroll bar and then we quit updating it
                        # until it's back at the bottom
                        if noscroll[1] > 0.98:
                            self.trafficbox.yview(tk.END)
                        self.trafficbox['state']='disabled'

                except Exception as e:
                    print(f"Error in node.manager() {e}") #TODO change to debug logging
        self.after(100, self.manager)

    def run(self):
        self.nt.start() # Start the Node Handling Thread
        self.after(100, self.manager)
        self.mainloop() # Start the GUI
        self.nt.stop()



if __name__ == "__main__":
    app = App()
    app.run()
