========================================
CAN-FiX Basic Firmware Download Protocol
========================================

The CAN-FiX Utility is capable of using multiple different protocols to download
firmware to nodes.  This chapter describes the *Basic* Firmware Download
Protocol.  This is a generic, general use protocol that can be implemented by
CAN-FiX nodes and used to load firmware into those nodes via the CAN Bus.

Overall Description
-------------------

Firmware is loaded into CAN-FiX nodes over a mechanism described in the CAN-FiX
specification  as a *Two Way Communication Channel*.  These channels are simply
a collection of CAN Frame IDs that are set asside for nodes to use for point to
point communication.  Mechanisms exist in the CAN-FiX specification for
allocating and using these channels.  See the CAN-FiX specification for details
concerning those mechanims.  Essentially, each node in the point to point
communication will be assigned one ID out of a pair of ID's.  One ID is used for
Host to Node messages and the other is used for Node to Host messages [#F1]_.

A firmware download is initiated when the host sends a *Firmware Update Command*
to the node.  The node would acknowledge this request and then wait to recieve
the first block of data. Firmware is transmitted to the node as a collection of
individual blocks.  The actual block size may be important to the receiving
node.  It is up to the developer to determine an appropriate block size for the
node in question.

The overall communication to write one block to the node is shown below.

::

  Host: Send Block ID Frame
  Node: Respond with Block ID Ack
  Host: Send Data Frame
  Node: Respond with Data Frame Ack
  Host: Send More Data Frames
  Node: Respond to Each Data Frame with Ack
  Host: Send Block End Frame
  Node: Respond with Block End Frame Ack

This sequence of frames would result in a single block being sent to the node.
Once all of the blocks have been sent a *Transmission Complete* frame would be
sent and the communication is over.  At this point the node is free to begin
execution of the new firmware.

Initialization
--------------

There are a couple of ways to get a node into a state where it is listening for
firmware.  The first is for the node to respond to the CAN-FiX message designed
for this purpose.  The CAN-FiX *Update Firware* Command assigns the channel
number and passes the verification code to a node to begin the process.  After
the node acknowledges this command [#F2]_ it should be gin listening for the
first data block transfer.

Another prefered way to get a node into a listening state is to have it start up
in that state and listen for an *Update Firmware* command to be sent to it.  If
after a second or two no command is received it can resume starting it's already
installed application firmware.

Any host program should send the *Update Firware* command repeatedly at least
twice per second to try and initialize a node in this state.  It is preferable that
the host continue to try until the user cancels the attempt.  This way, the host
software can be started and the firware update feature selected and started, then the node
can be powered up and the transfer should begin during this startup phase.

Including the start up feature solves a problem where an errant firmware load
would "brick" the node.  If we rely soley on the application firmware for this
feature then we won't have a method to recover from a failed or bug ridden
firmware load.

Before the application firmware is started, an integrity check of the program
should be performed.  Usually this would be some kind of checksum.  If the
integrity check fails the application should not be run.  At this point it may
make sense for the device to wait in a loop for an *Update Firware* command to
be sent. Some kind of indication of this state like a red flashing LED or a bad
status message being sent over the CAN Bus would also be nice to have.  This
indication obviously depends on what makes the most sense for the particular
device.

Frame Descriptions
------------------

Start Block Frame
*****************

.. tabularcolumns:: |c|p{2cm}|
.. table:: Start Block Frame

  ====    ===============
  Byte    Data
  ====    ===============
  0       Block Type
  1       Subsytem ID
  2       Block Size
  3       Addr0
  4       Addr8
  5       Addr16
  6       Addr24
  ====    ===============

To start the transmission of a block the host sends a *Start Blcok Frame* to the
Node.  The frame contains seven bytes of data.

The *Block Type* byte tells the node what type of block this will be.  This
is used primarily to determine where within the node the block should be written.
A node may have more than one memory that can be updated with this procedure
and the *Block Type* gives us a way to differnetiate between these memories.

The following table shows some suggested block types.

.. tabularcolumns:: |c|l|
.. table:: Block Types

  ==========    ===============
  Block Type    Description
  ==========    ===============
  0x00          Main Program Memory
  0x01          Main Data Memory
  0x02          Main Processor Configuration Memory
  0x03          External Program Memory
  0x04          External Data Memory
  0x10          Secondary CPU Main Program Memory
  0x11          Secondary CPU Main Data Memory
  0x12          Secondary CPU Processor Configuration Memory
  0x13          Secondary CPU External Program Memory
  0x14          Secondary CPU External Data Memory
  0xFC          Reserved for Previous Block Checksum
  0xFD          Reserved for End of Transmission Indication
  0xFE          Reserved for Abort Transmission Indication
  0xFF          Reserved for Error Indications
  ==========    ===============

These block types are suggested and as long as there is agreement between the
node and the host on what these mean, any block type can be used for this
purpose.  The exception to this is any block type that is described as Reserved.

The *Subsystem ID* allows for multiple locations of similar type.  For example a
system may have more than one external SPI Flash chip.  The Subsystem ID could
be used to differentiate between these.  Multiple Secondary CPUs could also be
addressed in this manner.  Again this is arbitrary as long as the host and the
node are in agreement.

The *Block Size* field indicates how much data the Node should expect in this
block before receiving a Block End Frame.  The block size is given as a power
of two.  Examples of some block sizes are given in the following table.

.. tabularcolumns:: |c|p{2cm}|
.. table:: Block Size Eamples

  ============    ===============
  Value Passed    Block Size
  ============    ===============
  0               1
  1               2
  2               4
  3               8
  4               16
  5               32
  10              1024 (1k)
  11              2048 (2k)
  ============    ===============

The last four fields are the destination address of the block.  4 GiB can be
addressed with this protocol.  The address is sent least significant byte first.
These addresses are given in bytes.  If a node addresses memory by words then
conversions will have to be done.

Once the Node determines that the block is appropriate it would send a Start
Block Acknowledge frame.  This frame is simply an echo of the Start Block Frame
that was sent from the host. If there is an error then the Node should respond
with the following frame.

.. tabularcolumns:: |c|p{2cm}|
.. table:: Start Block Error Response Frame

  ====    ===============
  Byte    Data
  ====    ===============
  0       0xFF
  1       Error Code
  ====    ===============

The following Error codes are defined.

.. tabularcolumns:: |c|l|
.. table:: Start Block Error Codes

  ====    ===============
  Code    Description
  ====    ===============
  0x00    Bad Block Type
  0x01    Wrong Subsystem ID
  0x02    Unsupported Block Size
  0x03    Bad Address
  ====    ===============

If an error is received by the host after a *Start Block Frame* the block should
not be sent.  It is up the host to determine if further blocks are appropriate
or possible.  The node will not be expecting data if it responds with an error,
it will be waiting for another Start Block Frame or an End Transmission Frame.

Data Frame
**********

After the *Start Block Frame* has been sent and acknowledged the host would
begin sending *Data Frames*.  These frames simply consist of one or more bytes
of data. The first frame of data would be written to the address given in the
*Start Block Frame* and subsequent bytes would be written to the memory in
sequential order.

After the node has successfully buffered or stored the data from the frame it
is to respond with a *Data Acknowledge Frame*.

.. tabularcolumns:: |c|p{2cm}|
.. table:: Data Acknowledge Frame

  ====    ===============
  Byte    Data
  ====    ===============
  0       Offset
  ====    ===============

The offset is the offset within the block as calculated by the node.  So the
first block of data would have a return offset of 0x00.  If eight bytes of
data were sent in the first block then the second Acknowledgement frame would
be 0x08 and so on.  This gives the host a way to determine if the node has missed
a particular block of data.  At that point the host can abort the transmission.

Block End Frame
***************

Once the final block of data has been sent the Host should send the *Block End
Frame*.  This is a frame with a DLC (Data Length Code) of zero.  This indicates
to the Node that the last frame of data has been sent and the Node can now write
the block to the final location.  Once the Node is ready for a new block of data
it should send the *Block End Frame Acknowledge* which is also a zero data length
frame.

Since the CAN-FiX protocol requires that nodes communicate on a channel
at least once every half second it may be necessary for the host to write
multiple Block End Frame messages on the bus to keep the channel alive while the
node writes the data to the final location.  Although it seems unlikely that a
node would need more than 500 mS to write that data to the final location it is
possible so this mechanism is provided.

Block Checksum
**************

If appropriate for the application, the host can follow the block with an
indication of what the checksum for the block should be.

.. tabularcolumns:: |c|p{2cm}|
.. table:: Previous Block Checksum

  ====    ===============
  Byte    Data
  ====    ===============
  0       0xFC
  1-4     Checksum
  ====    ===============

The type of checksum is outside the scope of this specification.  It can be
up to four bytes and should be sent LSB first.  This frame should be sent
immediately following the *Block End Frame* for each block that is sent.


Ending the Transmission
***********************

Once all of the blocks have been sent the Host would send a *Transmission
Complete Frame*.  This frame consists of one Byte of data and that byte should be
0xFD.  The node should immediately acknowledge this frame by echoing the frame
that same byte.  The node is now free to reset itself or start executing
the new firmware or configuration.

If the host detected an error in the trasmission, it can send a
*Transmission Abort Frame*  in lieu of the *Trasmission Complete Frame*.  This
frame is a single data byte frame and the data byte should be 0xFE.  The
behaviour that the node takes after getting an Abort from the host depends on
the individual node and how it is implemented.

To abort the transmission while data is being transferred and before the
complete block of data has been sent the *Transmission Abort Frame* should be
preceeded by a *Block End Frame* which is simply a zero length frame.

If the node writes the firmware to it's internal program memory block by block
then an abort means that it's program is probably flawed or incomplete and it
makes sense for that node to neglect the new firmware and simply spin in a loop
waiting for the host to try again.  However, if the node has the ability to
store the entire firmware and not make it permanent until it receives a
sucessfull *Transmission Compledte Frame* then it may execute the old firmware.
This all depends on the  implementation details of the individual node.

Notes
-----

This firmware loading procedure is meant for aircraft use, therefore, much
care should be taken to verify that the program sent is the program
that was received.  Typically this is done by calculating a checksum for the
program and verifying that the program located in program memory passes this
checksum before it is executed.  Some systems may periodically calculate
the checksum during execution.

Checksums for individual data packets were deliberatly left out of this
protocol.  CAN itself contains a checksum for the individual frames, so it is
assumed that once data is received it is correct.  The host can determine
whether the node received each frame in a data block by watching the offsets
returned by the node after each data frame.  If the node does not respond to a
given data frame the host can resend that frame and then check the returned
offset to make sure that the node and the host are still in agreement as to
which particular data block was sent.  If a descrepency is noted then the host
can send an end data block and start the block over.  At the end of this
procedure it is reasonalbe to assume that the data in that block was transmitted
correctly.

.. rubric:: Footnotes

.. [#F1] In this document the term *Host* is used to describe the computer that
  is running the configuration software to download the firmware and *Node* is
  used to describe the actual CAN-FiX node that will be updated.

.. [#F2] See the CAN-FiX documentation for details
