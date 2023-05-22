CAN-FIX is a CANBus based communication protocol designed for the exchange of
flight data between aircraft systems.  This project contains various utilities
that can be used to monitor, configure, troubleshoot and update devices that
implement this protocol.

Right now the dependencies for this project are...

Python 3.x  support for Python 2.x is deprecated.  It might work but I doubt it.

tkinter - GUI Library for Python

python-can - Used as the canbus interface.

The *Nodes* tab on the main screen will show which individual nodes are being
heard on the network.

The *Parameters* tab shows the parameters which are being heard on the network

The *Traffic* tab is used to monitor traffic on the bus menu.  The start/stop
buttons start and stop traffic monitoring and the Raw checkbox is used to toggle
between showing the raw CAN frame and the decoded CAN-FIX information.

Firmware can be downloaded to a particular node

Configuration key/value pairs can be set as well, as long as we have an EDS file
for the particular node.  The complete configuration for a node can be saved to
a file as well as loaded from a file.

The utility can also be used as a command line program.  This would aid in
automating configuration of nodes, downloading firmware and doing automated
testing.  This utility is **NOT** meant to be used in flight.  It is for
configuration and testing on the ground only.