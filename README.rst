CAN-FIX is a CANBus based communication protocol designed for the exchange of
flight data between aircraft systems.  This project contains various utilities
that can be used to monitor, configure, troubleshoot and update devices that
implement this protocol.

Right now the dependencies for this project are...

Python 2.7 - I have not tried it with older (or newer versions) but it'll
probably work with 2.6.

PyQt5 - The program will revert to an interactive command line program if
PyQt5 is not available but the functionality is limited.

python-can - Used as the canbus interface.

The Data tab on the main screen will show the actual flight data that is
currently seen on the network.

The Network tab gives more detailed information about the state of the
network.

To monitor traffic on the bus make a connection to an adapter from the Comm
menu, and select the Traffic tab on the main screen.  The start/stop buttons
start and stop traffic monitoring and the Raw checkbox is used to toggle
between showing the raw CAN frame and the decoded CAN-FIX information.

Firmware downloading is done but not tested.  The current work is being
done on the Network tree view and the ability to monitor and configure
the network from this view.
