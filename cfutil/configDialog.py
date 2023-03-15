#!/usr/bin/env python

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

import sys
import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .ui.config_ui import Ui_dialogConfig
from . import config
from . import devices
from . import firmware

log = logging.getLogger(__name__)


class configListBox(QComboBox):
    def __init__(self, selections, value=None):
        QComboBox.__init__(self)

        for each in selections:
            x = selections[each]
            self.addItem(each, selections[each])
        for x in range(self.count()):
            if self.itemText(x) == value:
                self.setCurrentIndex(x)

    def value(self):
        return self.itemData(self.currentIndex())
        #return self.__value


def getConfigItemWidget(c, parent):
    """This function takes a configuration item from the networkModel and
       determines the type of widget that is needed to edit it"""
    generic_types = {"SHORT":(-128, 127),
                     "USHORT":(0, 255),
                     "INT":(-32768, 32767),
                     "UINT":(0, 65535),
                     "DINT":(-2147483648, 2147483647),
                     "UDINT":(0, 4294967296),
                     "FLOAT":(-2147483648, 2147483647)
                     }
    if c.input is not None:
        if c.input == "listbox":
            w = configListBox(c.selections, c.value)


    elif c.datatype in generic_types:
        t = generic_types[c.datatype]
        if c.multiplier >= 1.0:
            w = QSpinBox(parent)
            w.setSingleStep(int(c.multiplier))
            w.setMinimum(c.get("min", t[0]))
            w.setMaximum(c.get("max", t[1]))
            try:
                w.setValue(int(c.value))
            except:
                w.setValue(0)
        else:
            w = QDoubleSpinBox(parent)
            w.setSingleStep(float(c.multiplier))
            w.setMinimum(c.get("min", t[0]))
            w.setMaximum(c.get("max", t[1]))
            try:
                w.setValue(c.value)
            except:
                w.setValue(0.0)
    else:
        w = None
    return w


class dialogConfig(QDialog, Ui_dialogConfig):
    def __init__(self, netmodel, nodeid, key):
        QDialog.__init__(self)
        self.setupUi(self)
        # So hitting enter doesn't send the value or close the box
        Btn = self.buttonBox.button(QDialogButtonBox.Apply);
        Btn.setAutoDefault(False);
        Btn.setDefault(False);
        Btn = self.buttonBox.button(QDialogButtonBox.Close);
        Btn.setAutoDefault(False);
        Btn.setDefault(False);

        for node in netmodel.nodes:
            if node.nodeID == nodeid:
                self.node = node
                break
        for c in node.configuration:
            if c.key == key:
                self.configItem = c
                break
        self.labelConfig.setText(str(self.configItem.name))
        self.widget = getConfigItemWidget(self.configItem, self.scrollAreaWidgetContents)
        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.widget)
        if c.units is not None:
            l = QLabel(self.scrollAreaWidgetContents)
            l.setText(c.units)
            self.formLayout.setWidget(0, QFormLayout.FieldRole, l)


    def btnClick(self, btn):
        if btn == self.buttonBox.button(QDialogButtonBox.Apply):
            self.configItem.value = self.widget.value()
