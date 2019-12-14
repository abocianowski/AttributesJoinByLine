# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AttributesJoinByLine
                                 A QGIS plugin
 Plugin to create polygon
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-06-16
        copyright            : (C) 2019 by Adrian Bocianowski
                             : The plug-in created thanks to the financial support of <a href="http://geofabryka.pl/">Geofabryka Sp. z o.o.</a>
        email                : adrian@bocianowski.com.pl
        git                  : tracker=https://github.com/abocianowski/AttributesJoinByLine/issues
                             : repository=https://github.com/abocianowski/AttributesJoinByLine
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
from .tools.attributesJoinByLine import AttributesJoinByLine as att_class

from PyQt5.QtCore import QCoreApplication

class AttributesJoinByLine:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.plugin_dir = os.path.dirname(__file__)

        self.mainToolbar = self.iface.addToolBar(u'Attributes Join By Line')
        self.actions = []
        self.icon_path = ':/plugins/AttributesJoinByLine/icons/'

        self.attJoinByLine = att_class(self.iface, self.plugin_dir, self.mainToolbar, self.icon_path)

    def initGui(self):
        self.first_start = True

    def tr(self, message):
        return QCoreApplication.translate('&Attributes Join By Line', message)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Attributes Join By Line'),
                action)
            self.iface.removeToolBarIcon(action)
        
