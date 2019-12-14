# -*- coding: utf-8 -*-

# ***************************************************************************
#   This program is free software; you can redistribute it and/or modify    *
#   it under the terms of the GNU General Public License as published by    *
#   the Free Software Foundation; either version 2 of the License, or       *
#   (at your option) any later version.                                     *
# ***************************************************************************
#     begin                : 2019-09-17                                     *
#     copyright            : (C) 2019 by Adrian Bocianowski                 *
#     email                : adrian at bocianowski.com.pl                   *
# ***************************************************************************

import os

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QAction, QWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt5 import uic, QtWidgets

from qgis.core import QgsProject,QgsSpatialIndex,QgsPointXY, QgsGeometry, QgsField, QgsVectorLayer, QgsLayerTreeLayer, QgsFeature, NULL, QgsMapLayerType
from ..dialogs.attributes_join_by_line import AttributesJoinByLineDialog

class AttributesJoinByLine(QWidget):
    def __init__(self, iface, plugin_dir, mainToolbar, icon_path):
        QWidget.__init__(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.plugin_dir = plugin_dir
        self.mainToolbar = mainToolbar
        self.icon_path = icon_path

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'attributesjoinbyline{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&AttributesJoinByLine')

        self.dialog = AttributesJoinByLineDialog(self.iface.mainWindow())
        self.dialog.sourcelayer.currentTextChanged.connect(self.onComboBoxChanged)
        self.dialog.connectinglayer.currentTextChanged.connect(self.onComboBoxChanged)
        self.dialog.targetLayer.currentTextChanged.connect(self.onComboBoxChanged)
        self.dialog.runButton.setEnabled(False)
        self.dialog.runButton.pressed.connect(self.clickOk)
        self.dialog.cancel_button.setEnabled(False)
        self.dialog.cancel_button.pressed.connect(self.clickCanel)

        #Colors
        self.redColor = QColor(255, 0, 0)
        self.blackColor = QColor(0, 0, 0)
        self.greyColor = QColor(65, 105, 225)
        self.greenColor = QColor(34, 139, 34)
        self.greyBlueColor = QColor(47, 79, 79)

        self.first_start = None

        self.initGui()

    def tr(self, message):
        return QCoreApplication.translate('AttributesJoinByLine', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
        checkable=False,
        checked=False,
        shortcut=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.mainToolbar.addAction(action)

        if checkable:
            action.setCheckable(True)
            
        if checked:
            action.setChecked(1)

        if shortcut:
            action.setShortcut(shortcut)

        self.actions.append(action)

        return action

    def addMissingColumns(self, sourceLayer, targetLayer):
        trLayer_fields = []

        srFields = sourceLayer.fields()
        trFields = targetLayer.fields()

        for i in trFields:
            name = str(i.name())
            typeName = str(i.typeName())
            tpl = [name,typeName]
            trLayer_fields.append(tpl)

        for i in srFields:
            name = str(i.name())
            typeName = str(i.typeName())
            tpl = [name,typeName]
            if tpl not in trLayer_fields:
                pr = targetLayer.dataProvider()
                pr.addAttributes([i])
                targetLayer.updateFields()
                self.sendDialogLog(f'   Missing field - the field {tpl} did not appear in the target layer and was added',self.greyBlueColor)

    def clearLog(self):
        for row in reversed(range(0,self.dialog.log.rowCount())):
            self.dialog.log.removeRow(row)

    def clickCanel(self):
        self.task.stopTask = True
        self.task.terminate()
        
        QMessageBox.warning(self.dialog ,'Canceling the process', 'The process has been stopped')
        self.dialog.progressBar.setValue(0)
        self.dialog.runButton.setEnabled(True)
        self.dialog.cancel_button.setEnabled(False)

    def clickOk(self):
        self.dialog.runButton.setEnabled(False)
        self.dialog.cancel_button.setEnabled(True)

        self.dialog.tabs.setCurrentIndex(1)
        self.clearLog()
        self.sendDialogLog('running proces...',self.greenColor)

        #Layers
        self.sourceLayer = self.pointLayersList[self.dialog.sourcelayer.currentIndex ()-1]
        self.connectinglayer = self.lineLayersList[self.dialog.connectinglayer.currentIndex ()-1]
        self.targetLayer = self.pointLayersList[self.dialog.targetLayer.currentIndex ()-1]
        
        self.addMissingColumns(self.sourceLayer, self.targetLayer)

        self.task = worker(self.sourceLayer, self.connectinglayer, self.targetLayer)
        self.task.log.connect(self.taskLog)
        self.task.changeFeature.connect(self.taskChangeFeature)
        self.task.progress.connect(self.taskProgress)
        self.task.finished.connect(self.taskFinished)
        self.task.start()

    def initGui(self):
        #Run Button 
        # <div>Icons made by 
        # <a href="https://www.flaticon.com/authors/srip" 
        # title="srip">srip</a> from <a href="https://www.flaticon.com/" 			    
        # title="Flaticon">www.flaticon.com</a> is licensed by 
        # <a href="http://creativecommons.org/licenses/by/3.0/" 			    
        # title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a></div>
        self.RunButton = self.add_action(
                self.icon_path + 'AttributesJoinByLine.png',
                text=self.tr(u'Attributes Join by Line'),
                callback=self.run,
                parent=self.iface.mainWindow(),
                enabled_flag = True,
                checkable=False)

        self.first_start = True

    def onComboBoxChanged(self):
        color = 'rgb(233,150,122)'
        sender = self.sender()
        if sender.currentText() != '':
                sender.setStyleSheet('')
        else:
                sender.setStyleSheet(f'background-color: {color}')
            
        if self.dialog.sourcelayer.currentText() =='' or self.dialog.connectinglayer.currentText() =='' or self.dialog.targetLayer.currentText() =='':
            self.dialog.runButton.setEnabled(False)
        else:
            self.dialog.runButton.setEnabled(True)

    def run(self):
        if self.first_start == True:
            self.first_start = False

        self.dialog.progressBar.setValue(0)

        # update combo box
        self.dialog.sourcelayer.clear()
        self.dialog.connectinglayer.clear()
        self.dialog.targetLayer.clear()

        self.dialog.sourcelayer.addItem(None)
        self.dialog.connectinglayer.addItem(None)
        self.dialog.targetLayer.addItem(None)

        self.pointLayersList = []
        self.lineLayersList = []

        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayerType.VectorLayer: #Vector layers
                if layer.wkbType() == 1: #Point
                    self.pointLayersList.append(layer)
                    self.dialog.sourcelayer.addItem(layer.name())
                    self.dialog.targetLayer.addItem(layer.name())

                if layer.wkbType() in (5,2): #MultiLineString, Linestring
                    self.lineLayersList.append(layer)
                    self.dialog.connectinglayer.addItem(layer.name())

        self.dialog.tabs.setCurrentIndex(0)
        self.dialog.show()
                                    
    def sendDialogLog(self, text, color, layer = None, feature = None):
        rowCount = self.dialog.log.rowCount()

        item = QTableWidgetItem(text)
        item.setForeground(color)

        self.dialog.log.insertRow(rowCount)
        self.dialog.log.setItem(rowCount,1, item)

        if layer != None and feature != None:
            button = QPushButton('Show on map')
            button.clicked.connect(lambda:self.showOnMap(layer,feature))
            self.dialog.log.setCellWidget(rowCount,0, button)

        self.dialog.log.selectRow(rowCount)

    def showOnMap(self,layer,feature):
        layer.removeSelection()
        layer.selectByIds([feature.id()])
        self.canvas.zoomToSelected(layer)
        self.canvas.refresh()

    def taskChangeFeature(self, data):
        self.targetLayer.startEditing()
        fields = self.sourceLayer.fields()
        tFields = self.targetLayer.fields()

        for d in data:
            feature = d[0]
            att = d[1]
            for e, f in enumerate(fields):
                idx = tFields.indexFromName(f.name())
                self.targetLayer.changeAttributeValue(feature.id(), idx, att[e])

        self.targetLayer.commitChanges()

    def taskFinished(self, data):
        self.dialog.runButton.setEnabled(True)
        self.dialog.cancel_button.setEnabled(False)

        self.sendDialogLog('process has been completed',self.greenColor)
        self.task.terminate()

        if self.dialog.addLayersWithError.isChecked():
            failPoints = data[0]
            failMultilines = data[1]

            if len(failPoints) != 0 or len(failMultilines) != 0:
                for l2rem in QgsProject.instance().mapLayersByName('AJBL_error_target_points'):
                    QgsProject.instance().removeMapLayer(l2rem)

                epsg = self.targetLayer.sourceCrs().authid()
                layer = QgsVectorLayer(f'Point?crs={epsg}', 'AJBL_error_target_points' , 'memory')
                QgsProject.instance().addMapLayer(layer, False)
                layerTree = self.iface.layerTreeCanvasBridge().rootGroup()
                layerTree.insertChildNode(0, QgsLayerTreeLayer(layer))
                layer.dataProvider().addAttributes([QgsField('Fail', QVariant.String)])
                
                for f in failPoints:
                    layer.startEditing()
                    feature = QgsFeature()
                    feature.setGeometry( f[0].geometry())
                    feature.setAttributes([f[1]])
                    layer.addFeature(feature)
                    layer.commitChanges()

                for f in failMultilines:
                    layer.startEditing()
                    feature = QgsFeature()
                    feature.setGeometry( f[0].geometry())
                    feature.setAttributes([f[1]])
                    layer.addFeature(feature)
                    layer.commitChanges()
                
                layer.reload()

    def taskLog(self, d):
        self.sendDialogLog(d[0], d[1], d[2], d[3])

    def taskProgress(self, val):
        self.dialog.progressBar.setValue(val)

class worker(QThread):
    log = pyqtSignal(list)
    changeFeature = pyqtSignal(list)
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, sourceLayer, connectingLayer, targetLayer):
        QThread.__init__(self)

        self.sourceLayer = sourceLayer
        self.connectingLayer = connectingLayer
        self.targetLayer = targetLayer

        self.stopTask = False

        self.redColor = QColor(255, 0, 0)
        self.greenColor = QColor(34, 139, 34)
        self.prg = 0

    def run(self):
        tFeturesCount = self.targetLayer.featureCount()

        connectinglayer_index = QgsSpatialIndex(self.connectingLayer.getFeatures())
        sourcePoint_index = QgsSpatialIndex(self.sourceLayer.getFeatures())

        failPoints = []
        failMultilines = []
        featureToChange = []
        log = []

        for p, targetPointfeature in enumerate(self.targetLayer.getFeatures()):
            if self.stopTask: 
                break
                return
            
            targetGeometry = targetPointfeature.geometry().asPoint()
            nearestLinesIdx = connectinglayer_index.nearestNeighbor(targetGeometry,0)
            nearestLinesIdxCount = len(nearestLinesIdx)

            if nearestLinesIdxCount == 0:
                self.log.emit(['No connected lines found',self.redColor, self.targetLayer, targetPointfeature])
                failPoints.append([targetPointfeature,'No connected lines found'])
                continue

            # Check touches line to source point layer
            lineTouches = []
            for line in nearestLinesIdx:
                linegeometry = self.connectingLayer.getFeature(line).geometry().mergeLines()
                if linegeometry.intersects(targetPointfeature.geometry()):
                    try:
                        linegeometry = linegeometry.asPolyline()
                    except:
                        self.log.emit(['The line found is of the multilinestring type. Linestring type is allowed',self.redColor, self.targetLayer, targetPointfeature])
                        failMultilines.append([targetPointfeature,'The line found is of the multilinestring type. Linestring type is allowed'])
                    
                    lineTouches.append(linegeometry)

            if len(lineTouches) == 0:
                self.log.emit(['No connected lines found', self.redColor, self.targetLayer, targetPointfeature])
                failPoints.append([targetPointfeature,'No connected lines found'])

            elif len(failMultilines) ==0:
                # Find connected points with data using line
                nearestSourcePoints = []
                for line in lineTouches:
                    for point in line:
                        nearestSourcePoint = sourcePoint_index.nearestNeighbor(point,0)
                        if nearestSourcePoint != []:
                            nearestSourcePoints.append(nearestSourcePoint)


                nearestSourcePointsCount = len(nearestSourcePoints)
                if nearestSourcePointsCount == 0:
                    self.log.emit(['No targets points were found using the line', self.redColor, self.targetLayer, targetPointfeature])
                    failPoints.append([targetPointfeature,'No targets points were found using the line'])
    
                elif nearestSourcePointsCount < len(lineTouches):
                    self.log.emit(['One of the lines is not connected to the source point', self.redColor, self.targetLayer, targetPointfeature])
                    failPoints.append([targetPointfeature,'One of the lines is not connected to the source point'])
                
                elif nearestSourcePointsCount == 1:
                    sourceFeature = self.sourceLayer.getFeature(nearestSourcePoints[0][0])
                    featureToChange.append([targetPointfeature, sourceFeature.attributes()])
                    
                else:
                    #source points was founded  > 1
                    attributes = []
                    for point in nearestSourcePoints:
                        feature = self.sourceLayer.getFeature(point[0])
                        if attributes == []:
                            attributes = feature.attributes()
                            for i in range(0,len(attributes)):
                                a = [attributes[i]]
                                attributes[i] = a
                        else:
                            for i in range(0,len(attributes)):
                                attributes[i].append(feature.attributes()[i])
                                attributes[i] = list(set(attributes[i]))

                    fail = 0
                    fail_fields = []
                    attributes_tmp = []
                    i = 0

                    for a in attributes:
                        a = tuple(a)
                        b = list(dict.fromkeys(a))
                        items = [None,NULL,'']
                        if len(b)>1:
                            for item in items:
                                b = [i for i in b if i != item]
                        if len(b) > 1:
                            fail += 1
                            fail_fields.append(self.sourceLayer.fields()[i].name())
                        attributes_tmp.append(b)
                        i +=1

                    attributes = attributes_tmp

                    if fail == 0:
                        featureToChange.append([targetPointfeature, attributes])
                    else:
                        self.log.emit([f"""Can't add attributes from {str(nearestSourcePointsCount)} source objects. The fields: {fail_fields} have different values""", self.redColor, self.targetLayer, targetPointfeature])
                        failPoints.append([targetPointfeature,f"""Can't add attributes {str(nearestSourcePointsCount)} from source objects. The fields: {fail_fields} have different values"""])

            prg = int((p/tFeturesCount)*100)
            if abs(prg - self.prg) >=1:
                self.prg = prg
                self.progress.emit(prg)

        self.log.emit(['Saving data in progress...', self.greenColor, None, None])
        self.changeFeature.emit(featureToChange)
        self.progress.emit(100)
        self.finished.emit([failPoints, failMultilines])