#!/usr/bin/python3

from cfutil import connectTk
import tkinter as tk

if __name__ == "__main__":
    cd = connectTk.ConnectDialog(None)
    cd.mainloop()
    okay = cd.okay
    if okay:
        print(cd.interface)
        print(cd.arguments)
    cd.destroy()