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

import tarfile
import json
import intelhex
import io
import logging

log = logging.getLogger(__name__)

# Within the tar/gzipped file there should be one or more files.  This class
# is the base class for each file format that we supoprt.
class StandardFileBase():
    def __init__(self, filedef):
        # These are the defaults
        self.filename = filedef['name']
        self.offset = 0
        self.blocktype = 0
        self.subsystem = 0

        if 'offset' in filedef:
            self.offset = int(filedef['offset'])
        if 'block type' in filedef:
            self.blocktype = int(filedef['block type'])
        if 'subsystem' in filedef:
            self.subsystem = int(filedef['subsystem'])
        if 'block size' in filedef:
            self.blocksize = int(filedef['block size'])
        else:
            raise ValueError("blocksize is requireed")
        log.debug(f"File {self.filename} loaded: block type = {self.blocktype}, subsyste = {self.subsystem}, block size = {self.blocksize}")

    @property
    def blockcount(self):
        blocks = self.size // self.blocksize
        if self.size % self.blocksize != 0:
            return blocks+1
        return blocks

# These are the specific file format classes.
# This represents an IntelHex file
class IntelHexFile(StandardFileBase):
    def __init__(self, filedef, fobj):
        StandardFileBase.__init__(self, filedef)

        self.__ih = intelhex.IntelHex(fobj)
        self.offset = self.__ih.minaddr() # Since IntelHex files have this information
        self.size = self.__ih.maxaddr() - self.__ih.minaddr() + 1
        self.data = []

        for n in range(self.size):
            self.data.append(self.__ih[n])

# This represents the ASCII hex file format.  Each
# pair of characters represents one byte.  White
# space is ignored.
class HexFile(StandardFileBase):
    def __init__(self, filedef, fobj):
        StandardFileBase.__init__(self, filedef)
        self.data = []
        x = 0
        s = fobj.read()
        st = s.decode()
        for ch in st:
            if ch.isnumeric() or (ch >= 'A' and ch <= 'F'):
                if x % 2 == 0:
                    sum = int(ch, 16) * 16
                else:
                    sum += int(ch, 16)
                    self.data.append(sum)
                x += 1
        self.size = len(self.data)

# The List file format is for data that is actually contained
# in the index.json file itself.  This is for small amounts of
# data
class ListFile(StandardFileBase):
    def __init__(self, filedef):
        StandardFileBase.__init__(self, filedef)
        self.data = []

        for x in filedef['data']:
            if isinstance(x, int):
                self.data.append(x)
            else:
                try:
                    self.data.append(int(x, 16)) # Try Base16
                except:
                    self.data.append(int(x)) # Try Base 10
        self.size = len(self.data)

# TODO Add base64, binhex4 and binary file fomrats

# This class is used to load the CAN-FiX standard firmware file format.
# see the CFUtil manual for a description of this file
class StandardFileLoader():
    def __init__(self, filename):
        tf = tarfile.open(filename,'r')
        f = tf.extractfile("index.json")
        self.index = json.load(f)
        self.files = []
        self.totalsize = 0

        for file in self.index['files']:
            if file['type'] == 'intelhex':
                f = tf.extractfile(file['name'])
                nf = io.TextIOWrapper(f)
                ihf = IntelHexFile(file, nf)
                self.files.append(ihf)
            elif file['type'] == 'hex':
                f = tf.extractfile(file['name'])
                hf = HexFile(file, f)
                self.files.append(hf)
            elif file['type'] == 'uuencode':
                raise NotImplementedError(f"{file['type']} not yet implemented")
            elif file['type'] == 'binhex4':
                raise NotImplementedError(f"{file['type']} not yet implemented")
            elif file['type'] == 'binary':
                raise NotImplementedError(f"{file['type']} not yet implemented")
            elif file['type'] == 'list':
                lf = ListFile(file)
                self.files.append(lf)
            else:
                raise ValueError(f"Unknown file type {file['type']}")

            self.totalsize += self.files[-1].size


