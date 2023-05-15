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

class StandardFileBase():
    def __init__(self, filedef):
        # These are the defaults
        self.offset = 0
        self.blocktype = 0
        self.subsystem = 0

        if 'offset' in filedef:
            self.offset = int(filedef['offset'])
        if 'blocktype' in filedef:
            self.blocktype = int(filedef['block type'])
        if 'subsystem' in filedef:
            self.subsystem = int(filedef['subsystem'])
        if 'block size' in filedef:
            self.blocksize = int(filedef['block size'])
        else:
            raise ValueError("blocksize is requireed")

class IntelHexFile(StandardFileBase):
    def __init__(self, filedef, fobj):
        StandardFileBase.__init__(self, filedef)

        self.__ih = intelhex.IntelHex(fobj)


class HexFile(StandardFileBase):
    def __init__(self, filedef, fobj):
        StandardFileBase.__init__(self, filedef)
        print(fobj.read())


class ListFile(StandardFileBase):
    def __init__(self, filedef):
        StandardFileBase.__init__(self, filedef)
        print(filedef['data'])


class StandardFileLoader():
    def __init__(self, filename):
        tf = tarfile.open(filename,'r')
        f = tf.extractfile("index.json")
        self.index = json.load(f)
        self.files = []

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
            else:
                raise ValueError(f"Unknown file type {file['type']}")


