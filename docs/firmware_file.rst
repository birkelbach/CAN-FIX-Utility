==================================
Firmware File Format Specification
==================================

This chapter describes the file format that the CFUtil firmware loading
utilities use for describing the information and the mechanism for downloading
a particular file to a node.  This file format is not mandatory.  Individual
firmware drivers within CFUtil may use their own specific file type if needed.

Overall Description
-------------------

The firmware file is simply a compressed archive.  The archive should be a gzip
compressed tarball file.  The file can easily be made with the following
command.

``tar zcvf firmware.cfw index.json file1 file2``

This archive should contain at least one file.  A file named *index.json* which
is a JSON file that contains all of the information any other files that may be
contained in the archive and how they are to be loaded.

A typical *index.json* might look like this.

.. literalinclude:: index.json

The *index.json* file contains overall information such as a descriptive name
for the firmware archive and the Verification Code that should be used when the
CAN-FiX host initiates the transfer with the individual node.  The Verification
Code is used to make sure that we don't try to download firmware to a device for
which it was not intended.

The index also contains the information about each firmware file in the archive.
At a minimum each object in the files list should contain the name of the file
within the archive and the encoding type.  Possible encodings are...

  *  intelhex
  *  base64
  *  binhex4
  *  binary
  *  hex
  *  list

*intelhex*, *base64* and *binhex4* are simply files of the given type.  The
*binary* type file is simply a file that contains the bytes directly with no
formatting at all.  The *hex* encoding is an unformatted file that contains an
ASCII hex representation of each byte.  A *hex* file would be more than twice the
size of the same *binary* file since each byte would be converted into two
characters.  Carrage returns and line feeds would be ignored.

If the encoding is *list* the data to be written should be given in the json
object as a list named *data*.  Each item in the list should be a representation
of a single 8-bit byte of data.

This mechanism can be used to write serial numbers or calculated checksums
to specific places in memory without having to create an additional file
for that purpose.

*offset* is the memory offset where this file will be written.  Some file formats
(i.e. *IntelHex*) have address information contained within them.  In that case
this offset would be ignored.  For other file formats this offset will be the
starting address where the data in this file will be written.

The remainder of the information contained in each file object is protocol
specific. The example shows information that is needed for the Basic CAN-FiX
Firmware Protocol. Other protocols may have different information.  See the
individual protocol definitions for information that is required for each.

Because JSON does not allow for hexidecimal notation the bytes can ge given as
strings of hex.  i.e. "0x0F" and the program that reads this information should
make the conversions.
