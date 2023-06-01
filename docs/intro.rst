============
Introduction
============

FIX is an acronym for Flight Information eXchange.  It is a set of protocol
specifications for exchanging information between aircraft avionics and flight
systems.  This specification and the protocols themselves are licensed under a
Creative Commons license that allows anyone to modify and redistribute these
documents without charge.

This is a community supported endeavor, with the primary goal of providing a
standard method for avionics and flight control systems to communicate with one
other in a vendor neutral way.

These specifications and protocols are primarily geared toward the Experimental
Amateur Built (E-AB) aircraft community.  Keeping the specification open and
free allows airplane builders to create their own devices and write their own
software that will be able to communicate with other devices without need to pay
for specifications or licenses.  It also encourages collaboration in the
development and improvement of the protocols themselves.

CAN-FiX is the CAN Bus implementation of the FIX philosophy.  A full description
of CAN-FiX is beyond the scope of this manual.  For details on the CAN-FiX
protocol itself can be found in the official specification.

This manual describes the operation of CFUtil which is a generic utility for
configuring, monitoriing and troubleshooting a CAN-FiX network.

General Description
-------------------

CFUtil can be used as a graphical desktop application (GUI) or as a command line
utility.  By using the program as a command line utility many tasks can be automated,
such as loading firmware or loading / saving node configurations.