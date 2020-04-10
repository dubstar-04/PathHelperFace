import FreeCAD, FreeCADGui
import Part
import Draft
import os, math
import PathHelperFace

from PySide import QtGui, QtCore
from PySide.QtGui import QTreeWidgetItem

import PathScripts.PathUtils as PathUtils

dir = os.path.dirname(__file__)
ui_name = "PathHelperFace.ui"
path_to_ui = dir + "/" +ui_name

class PathHelperPanel:
	def __init__(self, obj=None):
		# self will create a Qt widget from the ui file
		self.form = FreeCADGui.PySideUic.loadUi(path_to_ui)
		self.tempObj = None
		self.helperFace = None

       #Load UI Components
		self.addFace_PB = self.form.addFace_PB
		self.face_LE = self.form.face_LE
		self.edges_TW = self.form.edges_TW
		self.extendDist_LE = self.form.extendDist_LE
		self.toolController_CB = self.form.toolController_CB
		self.apply_PB = self.form.apply_PB

		##setup ui
		self.edges_TW.headerItem().setText(0, "Extendable Edges")
      
        #connect
		self.addFace_PB.clicked.connect(self.handleSelection)
		self.edges_TW.itemClicked.connect(self.edgeSelected)
		self.apply_PB.clicked.connect(self.extendFace)
		#self.toolController_CB.currentIndexChanged.connect(self.updateTool)

		if obj:
			self.helperFace = obj
			self.setFaceName(self.helperFace.BaseFace[0], self.helperFace.BaseFace[1][0])
			self.extendDist_LE.setText(str(obj.ExtraDist))
			self.buildEdgeList()
		else:
			#try and load and preselected faces
			self.extendDist_LE.setText(str(0.0))
			self.handleSelection()

	def setFaceName(self, baseModel, faceName):
		objName = baseModel.Name
		modelFaceName = objName + '.' + faceName 
		self.face_LE.setText(modelFaceName)

	def handleSelection(self):
		sel = None
		try:	
			sel = FreeCADGui.Selection.getSelectionEx()[0]
		except:
			pass
		if sel:
			for subName in sel.SubElementNames:
				if 'Face' in subName:
					self.setFaceName(sel.Object, subName)
					self.helperFace = self.create((sel.Object, subName)) 
					self.buildEdgeList()
					
				if 'Edge' in subName:
					FreeCAD.Console.PrintError('Edge Selection Not Currently Supported')

	def buildEdgeList(self):
		''' populate the ui tree with the edges that can be extended'''
		self.edgeList = []

		treeExists = False
		if self.edges_TW.topLevelItem(0):
			treeExists = True
			parentItem =self.edges_TW.topLevelItem(0)
		else:
			self.edges_TW.clear()
			parentItem =  QTreeWidgetItem()
			faceName = self.face_LE.text()
			parentItem.setText(0, faceName)
			self.edges_TW.addTopLevelItem(parentItem)
			self.edges_TW.expandItem(parentItem)

			if not treeExists:
				for edgeNum in self.helperFace.ExtendableEdges:
					###### populate the edge tree ######
					edgeItem =  QTreeWidgetItem()
					edgeItem.setText(0, str("Edge" + str(edgeNum)))
					checked = QtCore.Qt.Unchecked
					if edgeNum in self.helperFace.CheckedEdges:
						checked = QtCore.Qt.Checked
					edgeItem.setCheckState(0, checked)
					parentItem.addChild(edgeItem)

		self.loadTools()

	def edgeSelected(self, item):
		'''handle edge selection in the tree'''
		edgeName = item.text(0)
		FreeCADGui.Selection.clearSelection()
		FreeCADGui.Selection.addSelection(self.helperFace, edgeName)
	
	def extendFace(self):

		self.updateTool()

		treeFace = self.edges_TW.topLevelItem(0)	
		edgeCount = treeFace.childCount()
		checkedEdges = []
		for i in range(edgeCount):
			if treeFace.child(i).checkState(0) == QtCore.Qt.CheckState.Checked:
				edgeNumber = int(treeFace.child(i).text(0).replace('Edge', ''))
				checkedEdges.append(edgeNumber)
				
		self.helperFace.ExtraDist = float(self.extendDist_LE.text())
		self.helperFace.CheckedEdges = checkedEdges
		FreeCAD.ActiveDocument.recompute()
		
	def loadTools(self):
		job = PathUtils.findParentJob(self.helperFace.BaseFace[0])
		self.toolController_CB.addItem('None')
		for idx, tc in enumerate(job.ToolController):					
			self.toolController_CB.addItem(tc.Name)
			
			if self.helperFace.ToolController:
				if tc.Name == self.helperFace.ToolController.Name:
					self.toolController_CB.setCurrentIndex(idx + 1)

	def getToolController(self):
		job = PathUtils.findParentJob(self.helperFace.BaseFace[0])
		tcStr = self.toolController_CB.currentText()
		for tc in job.ToolController:
			if tc.Name == tcStr:
				return tc
		
		return None

	def updateTool(self):
		tc = self.getToolController()
		self.helperFace.ToolController = tc
		
	def create(self, baseFace):
		faceName = self.face_LE.text()
		helperFaceName = faceName + '_Helper'
		obj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', helperFaceName)
		
		PathHelperFace.HelperFace(obj, baseFace)
		PathHelperFace.ViewProviderHelperFace(obj.ViewObject)
		FreeCAD.ActiveDocument.recompute()
		self.tempObj = obj.Name
		return obj

	def reject(self):
		if self.tempObj:
			FreeCAD.ActiveDocument.removeObject(self.tempObj) 
		self.quit()

	def accept(self):
		FreeCAD.Console.PrintMessage("\nAccept Signal")
		self.quit()
    
	def quit(self):
		FreeCADGui.Control.closeDialog(self)