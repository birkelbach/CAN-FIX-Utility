============
Development
============


CAN Bus Connection
-------------------

The ``cfutil.connection.canbus`` object will be instantiated when the
``cfutil.connection`` module is imported for the first time.

There are two ways to interact with the CAN bus.  The first is to request
a Connection from the canbus object.  The returned object has a ``send`` and a
``recv`` method that can be used just like we have our own personally access to
the CAN Bus.  The Connection object that is returned from the canbus.get_connection
method is essentially nothing more than a queue that acts like our own CAN bus.
The send funciton simply sends a message through the Bus if it is connected.


The second way to interact with the CAN bus is to define the
``canbus.recvMessageCallback`` member of the ``canbus`` object.  There is only one
callback.  It takes one argument and that is the python-can message that was
received.

These two methods can be used together but care should be taken to remove the
message frome the recieve queue by calling the ``recv`` function of the
connection object to keep the queue from filling up.

Node Thread
-------------

The status of the network is kept in a thread derived from the class
``nodes.NodeThread``.  This is only used when the GUI is launched.  When
the program is run as a command line utility the thread is not used.
This is essentially a thread that maintains a picture of the current state
of the network.  It continuously receives messages from the network and
determines what to do with those messages.

If the message is from a Node that it has not heard from before, the NodeThread
will add that node to the list and try to identify it.  It sends a CAN-FiX
Noide Identification message to the node to request it's identifying information.
When that is received the it will try to retrieve a device definition
from the ``devices`` module.  The node will be listed and any status messages
that are received from that node will be decoded and stored.  If there is
no device definition for the new node it will still be monitored and maintained,
but without the identifying information and features that would be available
to a node that has a proper EDS file loaded.

A list of Nodes and a dictionary of received Parameters is kept in the
NodeThread.  There are also various callbacks associated with the
addition, removal and updating of these Nodes and Parameters.

Node Data
---------

Node data (mostly EDS files) are maintained globally.  There is an index
that is currently made available, and this index contains the information
that is necessary to download the rest of the data.  The main configuration
file should have ``data_index_uri`` that contains a Uniform Resource
Identifier of the location of the index file.  The index file can
be any URI that urllib.request method can access and this includes local
files.  Local files can be used for development and testing.  See the
``canfix-data`` GitHub project for more information on this index and
the methods of distributing this data.

EDS files are loaded from a directory derived from the path that is
returned by ``appdirs.user_data_dir``.  Usually '<data>/cfutil/eds'  Any
EDS files that are found here will be loaded whether or not they are in
the index.  They will not be automatically maintained but they will be
used by the program.

