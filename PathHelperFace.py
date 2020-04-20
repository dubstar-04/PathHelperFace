# -*- coding: utf-8 -*-

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2020 Daniel Wood <s.d.wood.82@googlemail.com>            *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import FreeCAD, FreeCADGui
import Part
import os, math

import PathScripts.PathUtils as PathUtils

import PathHelperFaceGui

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Icons' )

class HelperEdge:
	def __init__(self, edge, obj, fixedEdge = False):

		self._edge = edge
		self._obj = obj
		self._extendable = False
		self._fixedEdge = fixedEdge

	def _getEdge(self):
		return self._edge

	def _getMidParam(self):
		midparam = self._edge.FirstParameter + 0.5 * (self._edge.LastParameter - self._edge.FirstParameter)
		return midparam
	
	def _getMidPnt(self):
		''' get the mid point '''
		midpnt = self._edge.valueAt(self._getMidParam())
		return midpnt

	def _rotate(self, vec, angle):
		''' rotate point by angle in radians '''
		x = vec.x * math.cos(angle) - vec.y * math.sin(angle)
		y = vec.x * math.sin(angle) + vec.y * math.cos(angle)
		return FreeCAD.Vector(x, y, vec.z)

	def _getPerpNormal(self):
		''' get edge perpendicular normal at the mid point in the open direction'''
		midpnt = self._getMidPnt()
		axialNorm = self._edge.tangentAt(self._getMidParam())
		perpNormal = self._rotate(axialNorm, 1.5708)

		poffPlus = midpnt + 0.01 * perpNormal
		poffMinus = midpnt - 0.01 * perpNormal

		if self._obj.Shape.isInside(poffPlus, 0.005, False):
			perpNormal = perpNormal.negative()
		if self._obj.Shape.isInside(poffMinus, 0.005, False):
			pass

		return perpNormal

	def _isExtendable(self):
		''' check if the edge is extendable i.e. constrained by a connected face'''
		if self._fixedEdge:
			return False

		extendable = True
		midpnt = self._getMidPnt()
		perpNormal = self._getPerpNormal()

		poffPlus = midpnt + 0.01 * perpNormal
		poffMinus = midpnt - 0.01 * perpNormal

		if self._obj.Shape.isInside(poffPlus, 0.005, False):
			extendable =  False
		if self._obj.Shape.isInside(poffMinus, 0.005, False):
			extendable = False

		return extendable


class HelperFace:
	def __init__(self, obj, baseFace, toolController=None):

		obj.addProperty('App::PropertyLinkSub', 'BaseFace', 'Base', 'faceName').BaseFace = baseFace
		obj.addProperty('App::PropertyFloat', 'ExtraDist', 'Base', 'Additional Offset')
		obj.addProperty('App::PropertyIntegerList', 'CheckedEdges', 'Base', 'list of edges to extend')
		obj.addProperty('App::PropertyIntegerList', 'ExtendableEdges', 'Base', 'list of edges that can be extended')
		obj.addProperty("App::PropertyLink", "ToolController", "Base", "The tool controller that will be used to calculate the path")
		if toolController:
			obj.ToolController = toolController
		obj.Proxy = self

		obj.setEditorMode('CheckedEdges', 2)
		obj.setEditorMode('ExtendableEdges', 2)

	def onChanged(self, obj, prop):
		'''Do something when a property has changed'''
		#FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")
		pass

	def onDocumentRestored(self, obj):
		'''Do something when a document is restored'''
		pass

	def execute(self, obj):
		""" Called on document recompute """
		edgeManager = HelperEdgeManager() 
		helperEdges = edgeManager.getEdges(obj.BaseFace)

		if len(helperEdges) < 3:
			FreeCAD.Console.PrintError('Helper Face Generation Failed\n')
			return

		edges = []
		extendableEdges = []
		for idx, helperEdge in enumerate(helperEdges):
			if helperEdge._isExtendable():
				extendableEdges.append(idx+1)
			edge = helperEdge._getEdge()
			edges.append(edge)

		extendDist = 0

		if obj.ToolController:
			toolRad = obj.ToolController.Tool.Diameter * 0.5
			extendDist = toolRad
		
		extendDist += obj.ExtraDist
		
		obj.ExtendableEdges = extendableEdges
		newFace = edgeManager.createFace(edges)
		obj.Shape = edgeManager.extendFace(edges, obj.CheckedEdges, newFace, extendDist)


class ViewProviderHelperFace:
	def __init__(self, obj):
	   """
	   Set this object to the proxy object of the actual view provider
	   """
	   obj.Proxy = self

	def attach(self, obj):
	   """
	   Setup the scene sub-graph of the view provider, this method is mandatory
	   """
	   return
	   
	def setEdit(self, vobj, mode=0):
		# pylint: disable=unused-argument
		panel = PathHelperFaceGui.PathHelperPanel(vobj.Object)
		FreeCADGui.Control.showDialog(panel)
		return False
	
	def unsetEdit(self, vobj, mode=0):
		# pylint: disable=unused-argument
		return False

	def getIcon(self):
		return os.path.join( iconPath , 'Path_HelperFace.svg')

class HelperEdgeManager:
	def __init__(self):
		self.helperEdges = []

	def showEdge(self, edges):
		Wire = Part.Wire(edges)
		edgeName = 'testEdge'
		Part.show(Wire, edgeName) 
		FreeCAD.ActiveDocument.recompute()

	def getEndPoints(self):
		points = []
		for helperEdge in self.helperEdges:
			edge = helperEdge._getEdge()
			for v in edge.Vertexes:
				points.append(v.Point)

		### Find the two points that are not connected ###
		endPoints = []
		for p in points:
			if points.count(p) == 1:
				endPoints.append(Part.Vertex(p))

		return endPoints


	def getEdges(self, baseFace):
		model = baseFace[0]
		face = model.Shape.getElement(baseFace[1][0])
		wire = face.OuterWire
		job = PathUtils.findParentJob(model)
		
		stock = job.Stock
		bb = stock.Shape.BoundBox

		for edge in wire.Edges:
			newEdge = HelperEdge(edge, model)
			if not newEdge._isExtendable():
				self.helperEdges.append(newEdge)

		###### get boundingbox edges at face z height ######
		bbEdges=[]
		bbz = face.BoundBox.ZMax
		bbEdges.append(Part.Edge(Part.LineSegment(FreeCAD.Vector(bb.XMin,bb.YMin,bbz), FreeCAD.Vector(bb.XMin,bb.YMax,bbz))))
		bbEdges.append(Part.Edge(Part.LineSegment(FreeCAD.Vector(bb.XMin,bb.YMax,bbz), FreeCAD.Vector(bb.XMax,bb.YMax,bbz))))
		bbEdges.append(Part.Edge(Part.LineSegment(FreeCAD.Vector(bb.XMax,bb.YMax,bbz), FreeCAD.Vector(bb.XMax,bb.YMin,bbz))))
		bbEdges.append(Part.Edge(Part.LineSegment(FreeCAD.Vector(bb.XMax,bb.YMin,bbz), FreeCAD.Vector(bb.XMin,bb.YMin,bbz))))

		if not len(self.helperEdges):
			FreeCAD.Console.PrintWarning('Open Face Selected')
			objBBz = model.Shape.BoundBox.ZMax

			if round(bbz, 5) == round(objBBz, 5):
				FreeCAD.Console.PrintWarning('Top face of object selected')
				for edge in bbEdges:
					newEdge = HelperEdge(edge, model)
					self.helperEdges.append(newEdge)
			
				# Check if the helper edges are available and return
				if len(self.helperEdges):
					return self.helperEdges
			
		endPoints = self.getEndPoints()

		if not endPoints:
			## No end points generated, face generation failed, return the list of helper edges and exit cleanly. 
			return self.helperEdges
		else:
			## if a single fixed edge cannot be generated return all the edges from the selected face
			if len(endPoints) > 2:
				self.helperEdges = []
				for edge in wire.Edges:
					newEdge = HelperEdge(edge, model)
					self.helperEdges.append(newEdge)

				return self.helperEdges	

		## get edge edges ##
		stockIntersectPoints = []
		bbStockEdges = []
		bbConnEdges = []
		tempEdges = self.helperEdges.copy()
		for ep in endPoints:
			intersections = []
				
			for i, newEdge in enumerate(tempEdges):
				edge = newEdge._getEdge()
				for v in edge.Vertexes:	
					if self.isSamePoint(ep.Point, v.Point):	
						for bbedge in bbEdges:
							## get the intersection point with the stock edge
							if Part.Circle == type(edge.Curve):
								## get the direction of the end points
								tangent = edge.tangentAt(edge.FirstParameter).negative()
								if self.isSamePoint(ep.Point, edge.lastVertex().Point):
									tangent = edge.tangentAt(edge.LastParameter)
								normal = tangent
								# ## If the normal generates a point inside the model rotate the normal by 90 deg 
								testPoint = ep.Point + 0.01 * tangent

								## if the test point is inside the model take the normal from the circle centre to the end point.
								if model.Shape.isInside(testPoint, 0.005, True):
									normal = ep.Point.sub(edge.Curve.Location).normalize()

								endPoint = ep.Point + 5 * normal
								tempEdge = Part.Edge(Part.LineSegment(ep.Point, FreeCAD.Vector(endPoint.x, endPoint.y, endPoint.z)))
								intersectPts = tempEdge.Curve.intersectCC(bbedge.Curve)
							else:
								## edge is a line
								## get the normal if the element is a line
								normal = edge.lastVertex().Point.sub(edge.firstVertex().Point)
								if self.isSamePoint(ep.Point, edge.firstVertex().Point):
									normal = edge.firstVertex().Point.sub(edge.lastVertex().Point)

								normal = normal.normalize()
								intersectPts = edge.Curve.intersectCC(bbedge.Curve)

							if len(intersectPts):
								for pnt in intersectPts:
									tempPnt = FreeCAD.Vector(pnt.X, pnt.Y, pnt.Z)
									posOnEdge = bbedge.Curve.parameter(tempPnt)
									if not posOnEdge < 0 and not posOnEdge > bbedge.LastParameter:
										intersections.append(pnt)
										bbStockEdges.append(bbedge)
										vectorCompare = tempPnt.sub(v.Point).normalize()
										dist = vectorCompare.sub(normal).Length

										if dist < 0.01:
											extEdge = Part.Edge(Part.LineSegment(ep.Point, tempPnt))
											newEdge = HelperEdge(extEdge, model, True)
											self.helperEdges.append(newEdge)
											bbConnEdges.append(bbedge)
											stockIntersectPoints.append(tempPnt)	

		###### check if the bb edges are the same edge ######
		if len(bbConnEdges) == 2:
			if bbConnEdges[0] == bbConnEdges[1]:
				###### Create new connecting edge and add to the list of edges ######
				closeEdge = Part.Edge(Part.LineSegment(stockIntersectPoints[0], stockIntersectPoints[1]))
				newEdge = HelperEdge(closeEdge, model)
				self.helperEdges.append(newEdge)
			else:				
				###### check if the bb edges are connected ######
				bbEdgesConnected = False
				for v1 in bbConnEdges[0].Vertexes:
					for v2 in bbConnEdges[1].Vertexes:
						if self.isSamePoint(v1.Point, v2.Point):
							bbEdgesConnected = True
							###### Create new edges to the stock and add to the list of edges ######
							for pnt in stockIntersectPoints:
								edge = Part.Edge(Part.LineSegment(pnt, v1.Point))
								newEdge = HelperEdge(edge, model)
								self.helperEdges.append(newEdge)

				if not bbEdgesConnected:
					offsetDir = FreeCAD.Vector()
					edgeNormals = []
					for helperEdge in self.helperEdges:
						edgeNormals.append(helperEdge._getPerpNormal())

					for edgeVec in edgeNormals:
						offsetDir.x += edgeVec.x
						offsetDir.y += edgeVec.y
						offsetDir.z += edgeVec.z

					offsetDir = offsetDir.normalize()

					closingPts = []
					for i, pnt in enumerate(stockIntersectPoints):
						for v in bbConnEdges[i].Vertexes:
							vectorCompare = v.Point.sub(pnt).normalize()
							dist = vectorCompare.sub(offsetDir).Length

							#if self.isSamePoint(offsetDir, vectorCompare):
							if dist < 0.5: #TODO: Is checking the dist robust?
								closingPts.append(v.Point)
								edge = Part.Edge(Part.LineSegment(pnt, v.Point))
								newEdge = HelperEdge(edge, model)
								self.helperEdges.append(newEdge)
						
					if len(closingPts) == 2:
						edge = Part.Edge(Part.LineSegment(closingPts[0], closingPts[1]))
						newEdge = HelperEdge(edge, model)
						self.helperEdges.append(newEdge)

		if len(self.helperEdges):
			self.sortEdges()
			return self.helperEdges
		
		return face.Edges

	def sortEdges(self):
		''' sort the helper edges into a continous loop '''
		fcEdges = []
		for helperEdge in self.helperEdges:
			edge = helperEdge._getEdge()
			fcEdges.append(edge)

		sortedEdges = Part.__sortEdges__(fcEdges)
		sortedHelperEdges = []

		for edge in sortedEdges:
			for helperEdge in self.helperEdges:
				v1_1 = edge.firstVertex()
				v1_2 = edge.lastVertex()
				v2_1 = helperEdge._getEdge().firstVertex()
				v2_2 = helperEdge._getEdge().lastVertex()

				if self.isSamePoint(v1_1.Point, v2_1.Point) and self.isSamePoint(v1_2.Point, v2_2.Point) \
					or	self.isSamePoint(v1_1.Point, v2_2.Point) and self.isSamePoint(v1_2.Point, v2_1.Point):
					sortedHelperEdges.append(helperEdge)

		self.helperEdges = sortedHelperEdges

	def createFace(self, edges):
		''' create a new face using from the supplied edges'''
		finalWire = Part.Wire(edges)
		if not finalWire.isClosed():
			FreeCAD.Console.PrintError('Face Creation failed - wire not closed')
			self.showEdge(edges)
			return None
		else:		
			nface = Part.Face(finalWire, "Part::FaceMakerBullseye")
	
		return nface

	def isSamePoint(self, pt1, pt2):
		''' Checks if two points share the same coordinates '''
		if round(pt1.x, 5) == round(pt2.x, 5):
			if round(pt1.y, 5) == round(pt2.y, 5):
				if round(pt1.z, 5) == round(pt2.z, 5):
					return True
		
		return False

	def extendFace(self, edges, checkedEdges, face, extendDist=0):
		''' extend the selected edges '''

		newEdges = edges
		if len(checkedEdges):
			for e in checkedEdges:
				origEdge = newEdges[int(e) -1]
				if origEdge:
					p1 = origEdge.Vertexes[0].Point
					p2 = origEdge.Vertexes[1].Point

					## work out the direction the edge needs to be extended
					vec = p2.sub(p1)
					offsetDir = self.rotate(vec, 1.5708)
					offsetDir = offsetDir.normalize()
					cen = face.BoundBox.Center
					if cen.distanceToPoint(p1.add(offsetDir)) <  cen.distanceToPoint(p1):
						offsetDir = offsetDir.negative()
				
					## the direction is a normalised vector. multiply that by the distance required
					offset = offsetDir.multiply(extendDist)

					for i, repEdge in enumerate(newEdges):
						rev = repEdge.Vertexes
						for j, v in enumerate(rev):
							jOpp = 1 - j
							if self.isSamePoint(v.Point, p1) or self.isSamePoint(v.Point, p2):
								tempVerts = newEdges[i].Vertexes
								newEdge = Part.Edge(Part.LineSegment(tempVerts[j].Point.add(offset), tempVerts[jOpp].Point))
								newEdges.pop(i)
								newEdges.insert(i, newEdge)

		## clear the selection to ensure no weird graphics
		FreeCADGui.Selection.clearSelection()
		newFace = self.createFace(newEdges)
		if not newFace:
			FreeCAD.Console.PrintError('Face Extension Failed')
		else:
			return newFace
		
	def rotate(self, vec, angle):
		''' rotate the vector by the supplied angle in radians '''
		x = vec.x * math.cos(angle) - vec.y * math.sin(angle)
		y = vec.x * math.sin(angle) + vec.y * math.cos(angle)
		return FreeCAD.Vector(x, y, vec.z)

def create(baseFace):

	model = baseFace[0]
	job = PathUtils.findParentJob(model)
	doc = model.Document
	helperGrpName = job.Name + '_HelperGeometry'
	helperGrp = doc.getObject(helperGrpName)
	
	if not helperGrp:
		helperGrp = doc.addObject("App::DocumentObjectGroup", helperGrpName)

	objName = model.Name
	faceName = baseFace[1]
	modelFaceName = objName + '.' + faceName 	

	helperFaceName = modelFaceName + '_Helper'
	obj = helperGrp.newObject('Part::FeaturePython', helperFaceName)
	
	HelperFace(obj, baseFace)
	ViewProviderHelperFace(obj.ViewObject)
	FreeCAD.ActiveDocument.recompute()
	return obj