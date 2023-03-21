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
import can
import logging.config
import cfutil.config as config
from . import nodes
import tkinter as tk
import tkinter.ttk as ttk
import queue

# Command Queue commands
ADD_NODE = 1
DEL_NODE = 2
UPDATE_NODE = 3
ADD_PARAMETER = 4
DEL_PARAMETER = 5
UPDATE_PARAMETER = 6

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

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        nb = ttk.Notebook(self)
        self.cmd_queue = queue.Queue()

        nodeTab = cfTab(nb)
        parameterTab = cfTab(nb)
        dataTab = cfTab(nb)

        nb.add(nodeTab, text="Nodes")
        nb.add(parameterTab, text="Parameters")
        nb.add(dataTab, text="Data")
        
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
        nb.grid(row=0, column=0, sticky=tk.NSEW)

        x = self.nodeview.get_children()
        for each in x:
            print(each)

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
                        self.nodeview.set(str(cmd[1].nodeid)+".device", 'data', cmd[1].name)
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
            

        # curItem = self.nodeview.focus()
        # print(curItem)
        # item = self.nodeview.item(curItem) 
        # print(item)
        #print(self.nodeview.parent(curItem))
        self.after(1000, self.manager)

    def run(self):
        nt = nodes.NodeThread()
        nt.set_node_callbacks(self.add_node, self.del_node, self.update_node)
        nt.set_parameter_callbacks(self.add_parameter, self.del_parameter, self.update_parameter)
        nt.start()
        self.after(1000, self.manager)
        self.mainloop()
        nt.stop()


if __name__ == "__main__":
    app = App()
    app.run()
