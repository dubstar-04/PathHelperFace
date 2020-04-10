import FreeCAD, FreeCADGui
import Part
import Draft
import os, math
import PathHelperFaceGui

import PathScripts.PathUtils as PathUtils

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
		"""
	   	Return the icon in XMP format which will appear in the tree view. This method is optional and if not defined a default icon is shown.
	   	"""

		return """
	   		/* XPM */
			static char * vp_xpm[] = {
			"64 64 306 2",
			"  	c None",
			". 	c #0B1521",
			"+ 	c #0C1521",
			"@ 	c #0B1421",
			"# 	c #0C1621",
			"$ 	c #0B1622",
			"% 	c #0B1522",
			"& 	c #0C1622",
			"* 	c #101621",
			"= 	c #391922",
			"- 	c #6D1E25",
			"; 	c #9B2226",
			"> 	c #C92628",
			", 	c #DF2728",
			"' 	c #C12528",
			") 	c #A32226",
			"! 	c #842025",
			"~ 	c #671D24",
			"{ 	c #481A23",
			"] 	c #2A1722",
			"^ 	c #0F1621",
			"/ 	c #211722",
			"( 	c #571C24",
			"_ 	c #8C2025",
			": 	c #BA2427",
			"< 	c #E82929",
			"[ 	c #EF2929",
			"} 	c #EA2829",
			"| 	c #D02728",
			"1 	c #B22427",
			"2 	c #932126",
			"3 	c #761E25",
			"4 	c #191722",
			"5 	c #1F1722",
			"6 	c #4F1B23",
			"7 	c #801F25",
			"8 	c #B02427",
			"9 	c #E12728",
			"0 	c #DD2829",
			"a 	c #BE2427",
			"b 	c #A12226",
			"c 	c #821F25",
			"d 	c #641D24",
			"e 	c #451A23",
			"f 	c #271722",
			"g 	c #0E1521",
			"h 	c #0A1521",
			"i 	c #0B1620",
			"j 	c #0A1520",
			"k 	c #131521",
			"l 	c #3E1922",
			"m 	c #701E24",
			"n 	c #D12728",
			"o 	c #E92829",
			"p 	c #CD2628",
			"q 	c #7D1F25",
			"r 	c #1D1621",
			"s 	c #601C24",
			"t 	c #912126",
			"u 	c #EE2929",
			"v 	c #BD2527",
			"w 	c #711E24",
			"x 	c #261822",
			"y 	c #0B1621",
			"z 	c #521B24",
			"A 	c #791F25",
			"B 	c #A22226",
			"C 	c #CB2527",
			"D 	c #EB2829",
			"E 	c #301923",
			"F 	c #AA2327",
			"G 	c #2A1822",
			"H 	c #3F1922",
			"I 	c #E42829",
			"J 	c #0C1724",
			"K 	c #101E30",
			"L 	c #1B3555",
			"M 	c #244570",
			"N 	c #264976",
			"O 	c #203F66",
			"P 	c #1B3454",
			"Q 	c #152A43",
			"R 	c #101E31",
			"S 	c #0C1623",
			"T 	c #0D1726",
			"U 	c #14273E",
			"V 	c #1D395B",
			"W 	c #2E5B93",
			"X 	c #3465A4",
			"Y 	c #305D96",
			"Z 	c #294F7F",
			"` 	c #214168",
			" .	c #1A3251",
			"..	c #13243B",
			"+.	c #121521",
			"@.	c #371923",
			"#.	c #5F1C24",
			"$.	c #862025",
			"%.	c #AF2427",
			"&.	c #D72728",
			"*.	c #101F30",
			"=.	c #2B5487",
			"-.	c #3465A3",
			";.	c #3363A1",
			">.	c #2E5990",
			",.	c #1A3553",
			"'.	c #0C1825",
			").	c #230406",
			"!.	c #260102",
			"~.	c #210508",
			"{.	c #1C090E",
			"].	c #170D14",
			"^.	c #12101A",
			"/.	c #111C2E",
			"(.	c #1A3352",
			"_.	c #23446E",
			":.	c #2C558A",
			"<.	c #3363A2",
			"[.	c #2E588F",
			"}.	c #264A78",
			"|.	c #1F3C60",
			"1.	c #182D4A",
			"2.	c #111F33",
			"3.	c #3465A2",
			"4.	c #244770",
			"5.	c #13253B",
			"6.	c #0C1723",
			"7.	c #280000",
			"8.	c #260305",
			"9.	c #230C14",
			"0.	c #241A29",
			"a.	c #272F4C",
			"b.	c #2D4672",
			"c.	c #33609E",
			"d.	c #32619E",
			"e.	c #234570",
			"f.	c #1C3759",
			"g.	c #152942",
			"h.	c #0E1B2B",
			"i.	c #264A76",
			"j.	c #0B1623",
			"k.	c #1C385A",
			"l.	c #2B5285",
			"m.	c #314976",
			"n.	c #2E3759",
			"o.	c #2C253C",
			"p.	c #2A1320",
			"q.	c #280304",
			"r.	c #270101",
			"s.	c #23070B",
			"t.	c #22121C",
			"u.	c #232136",
			"v.	c #273759",
			"w.	c #2D5283",
			"x.	c #274D7C",
			"y.	c #162942",
			"z.	c #3463A1",
			"A.	c #32588E",
			"B.	c #304672",
			"C.	c #2E3252",
			"D.	c #2C2237",
			"E.	c #2A111B",
			"F.	c #280101",
			"G.	c #260203",
			"H.	c #24090F",
			"I.	c #231522",
			"J.	c #24253C",
			"K.	c #2A3F66",
			"L.	c #315C96",
			"M.	c #3463A0",
			"N.	c #325488",
			"O.	c #304068",
			"P.	c #2D2F4D",
			"Q.	c #2B1E31",
			"R.	c #29090F",
			"S.	c #250305",
			"T.	c #230B12",
			"U.	c #231827",
			"V.	c #262D49",
			"W.	c #2B446E",
			"X.	c #33609C",
			"Y.	c #3464A3",
			"Z.	c #3364A3",
			"`.	c #345E99",
			" +	c #314D7D",
			".+	c #2E395D",
			"++	c #2D2842",
			"@+	c #2B1726",
			"#+	c #280406",
			"$+	c #270001",
			"%+	c #24060A",
			"&+	c #24111B",
			"*+	c #242034",
			"=+	c #293759",
			"-+	c #2E5082",
			";+	c #3364A2",
			">+	c #32558A",
			",+	c #2F436D",
			"'+	c #2E314F",
			")+	c #2C1F33",
			"!+	c #2A0D16",
			"~+	c #280001",
			"{+	c #3263A2",
			"]+	c #3263A1",
			"^+	c #3262A1",
			"/+	c #324F80",
			"(+	c #2F3D63",
			"_+	c #2D2B46",
			":+	c #2B1929",
			"<+	c #3262A0",
			"[+	c #3161A0",
			"}+	c #3162A0",
			"|+	c #31619F",
			"1+	c #31609F",
			"2+	c #30609F",
			"3+	c #30609E",
			"4+	c #305F9E",
			"5+	c #2F5F9D",
			"6+	c #2F5E9D",
			"7+	c #2F5E9C",
			"8+	c #2E5D9C",
			"9+	c #2E5D9B",
			"0+	c #2E5E9C",
			"a+	c #2E5C9B",
			"b+	c #2D5C9B",
			"c+	c #2D5C9A",
			"d+	c #2D5B9A",
			"e+	c #2D5B99",
			"f+	c #2C5B99",
			"g+	c #2C5A99",
			"h+	c #2C5A98",
			"i+	c #2B5997",
			"j+	c #2B5998",
			"k+	c #2B5897",
			"l+	c #2B5896",
			"m+	c #2A5896",
			"n+	c #2A5795",
			"o+	c #295795",
			"p+	c #295694",
			"q+	c #295693",
			"r+	c #285593",
			"s+	c #295794",
			"t+	c #285592",
			"u+	c #285492",
			"v+	c #275492",
			"w+	c #295593",
			"x+	c #275491",
			"y+	c #275391",
			"z+	c #265390",
			"A+	c #265290",
			"B+	c #26528F",
			"C+	c #26518F",
			"D+	c #25518F",
			"E+	c #25518E",
			"F+	c #25508E",
			"G+	c #24508E",
			"H+	c #24508D",
			"I+	c #275390",
			"J+	c #244F8D",
			"K+	c #244F8C",
			"L+	c #234F8C",
			"M+	c #234E8C",
			"N+	c #234E8B",
			"O+	c #234D8B",
			"P+	c #224D8A",
			"Q+	c #224D8B",
			"R+	c #224C8A",
			"S+	c #224C89",
			"T+	c #214C89",
			"U+	c #214B89",
			"V+	c #214B88",
			"W+	c #204B88",
			"X+	c #204A87",
			"Y+	c #204A88",
			"Z+	c #1F467F",
			"`+	c #163259",
			" @	c #1B3F72",
			".@	c #132948",
			"+@	c #0C1624",
			"@@	c #1F4984",
			"#@	c #193865",
			"$@	c #11233C",
			"%@	c #1E447C",
			"&@	c #163054",
			"*@	c #0D1929",
			"=@	c #204986",
			"-@	c #1A3C6C",
			";@	c #122743",
			">@	c #270000",
			",@	c #1F4781",
			"'@	c #17345E",
			")@	c #0E1E32",
			"!@	c #280203",
			"~@	c #1C3F73",
			"{@	c #142B4A",
			"]@	c #0C1725",
			"^@	c #290000",
			"/@	c #28060A",
			"(@	c #290A10",
			"_@	c #2B1B2C",
			":@	c #2D2C47",
			"<@	c #325183",
			"[@	c #34629F",
			"}@	c #11253F",
			"|@	c #270102",
			"1@	c #220407",
			"                                                                                                                                ",
			"                                                                                                                                ",
			"                                                                                                                                ",
			"                                                                                                                                ",
			"                                                        . . . + @ #                                                             ",
			"                                              # $ . . . . . . . . . . . . . . . . %                                             ",
			"                                    & @ . . . . . * = - ; > , ' ) ! ~ { ] ^ . . . . . . . . + @ #                               ",
			"                            . . . . . . . / ( _ : < [ [ [ [ [ [ [ [ [ [ [ } | 1 2 3 ( = 4 . . . . . . . . . . . %               ",
			"                  . . . . . . . 5 6 7 8 9 [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ 0 a b c d e f g . . . . . . . h       ",
			"        i j . . . . . k l m b n [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ o p q r . . . . h       ",
			"  h . . . . . f s t ' } [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ u v w x . . . y y           ",
			"  h . . . . . + ] z A B C D [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ u v w x . . . y y                 ",
			"          # h . . . . . . * E ( q F | u [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ > q G . . . i %                       ",
			"                    & . . . . . . . . 4 H ~ _ : I [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ [ > q G . . . . . . . . . . . . %             ",
			"                    . . . . . . . J J . . . . . . / { - ; ' < [ [ [ [ [ [ [ [ > q G . . . K L M N O P Q R S . . . . . . . .     ",
			"          i j . . . . . T U V N W X X Y Z `  ...J . . . . . +.@.#.$.%.&.v w x . . . *.V =.-.X X X X X X X ;.>.,.'.. . . . .     ",
			"    ).!.~.{.].^./.(._.:.<.X X X X X X X X X X X <.[.}.|.1.2.% . . . . . . . . *.V =.-.X X X X X X X X 3.4.5.6.. . . *.V . .     ",
			"    7.7.7.7.7.7.7.8.9.0.a.b.c.X X X X X X X X X X X X X X X d.=.e.f.g.h.*.V =.-.X X X X X X X X -.i.U j.. . . K k.l.-.X . .     ",
			"    7.7.m.n.o.p.q.7.7.7.7.7.r.s.t.u.v.w.-.X X X X X X X X X X X X X X X X X X X X X X X X X x.y.j.. . . K k.l.-.X X X X . .     ",
			"    7.7.X X X X z.A.B.C.D.E.F.7.7.7.7.7.G.H.I.J.K.L.X X X X X X X X X X X X X X X X X x.y.j.. . . K k.l.-.X X X X X X X . .     ",
			"    7.7.X X X X X X X X X X M.N.O.P.Q.R.7.7.7.7.7.7.S.T.U.V.W.X.X X X X X X X X x.y.j.. . . K k.l.-.X X X X X X Y.Z.Z.Z.. .     ",
			"    7.7.X X X X X X X X X X X X X X X X `. +.+++@+#+7.7.7.7.7.$+%+&+*+=+-+i.U j.. . . K k.l.-.X X X X -.Y.Z.Z.Z.;+<.<.<.. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X z.>+,+'+)+!+~+7.7.7.7.7.~.. . *.V =.-.X X X Y.Z.Z.Z.Z.<.<.<.{+{+]+^+^+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X./+(+_+:+7.7.V =.-.X Y.Z.Z.Z.Z.;+<.<.{+{+]+^+^+^+^+<+[+[+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.Y.Z.Z.Z.Z.<.<.<.{+]+^+^+^+^+<+}+[+[+[+|+|+1+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.;+<.<.{+{+]+^+^+^+^+}+[+[+[+[+|+1+2+2+3+3+4+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.]+^+^+^+^+<+[+[+[+[+|+|+1+2+2+3+3+4+4+4+5+5+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.^+}+[+[+[+|+|+1+2+2+3+3+4+4+4+5+5+6+6+6+7+7+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.[+|+1+1+2+2+3+3+4+4+4+5+5+6+6+7+7+7+8+8+9+9+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.2+3+3+4+4+4+5+5+6+6+6+7+7+0+8+8+9+9+9+a+b+c+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.4+5+5+5+6+6+7+7+7+8+8+9+9+9+a+a+c+c+c+d+d+e+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.6+6+7+7+8+8+8+9+9+9+a+c+c+c+c+d+e+e+f+f+g+h+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.8+8+9+9+9+a+b+c+c+c+d+d+e+f+f+g+g+h+h+h+h+i+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.a+a+c+c+c+c+d+e+e+f+f+g+h+h+h+h+j+i+i+i+i+k+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.c+d+e+e+f+f+g+h+h+h+h+j+i+i+i+i+i+l+m+m+m+m+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.f+f+g+h+h+h+h+j+i+i+i+i+l+l+m+m+m+n+n+n+n+o+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.h+h+j+i+i+i+i+i+l+m+m+m+m+n+n+n+o+o+p+p+p+p+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.i+i+i+l+l+m+m+m+n+n+n+n+o+p+p+p+p+p+q+r+r+r+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.m+m+m+m+n+n+n+o+s+p+p+p+p+q+r+r+r+r+t+u+u+v+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.n+n+o+o+p+p+p+p+p+w+r+r+r+r+t+u+u+v+x+x+y+y+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.p+p+p+p+q+r+r+r+r+t+u+u+v+v+x+y+y+y+y+z+z+A+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.r+r+r+r+t+u+u+v+v+x+x+y+y+y+z+z+A+A+A+B+B+C+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.t+u+u+v+v+x+y+y+y+y+z+A+A+A+B+B+B+D+D+E+E+E+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.x+x+y+y+y+z+z+A+A+A+B+B+D+D+D+E+E+F+F+G+H+H+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.I+z+A+A+A+B+B+C+D+D+E+E+E+F+F+H+H+H+J+J+K+K+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.A+B+B+D+D+E+E+E+F+F+H+H+H+J+J+K+K+L+M+M+N+N+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.D+E+E+F+F+F+H+H+H+J+J+K+K+L+M+N+N+N+N+O+P+P+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.F+H+H+H+J+J+K+K+L+M+M+N+N+N+O+Q+P+P+P+P+R+S+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.J+K+K+K+L+M+N+N+N+N+O+P+P+P+P+R+S+S+T+T+U+V+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.M+M+N+N+N+O+Q+P+P+P+P+S+S+T+T+T+V+V+V+V+W+X+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.N+Q+P+P+P+P+R+S+T+T+T+U+V+V+V+W+Y+X+X+X+Z+`+. .     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.P+R+S+S+T+T+T+V+V+V+V+W+X+X+X+X+X+X+ @.@+@. . j     ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.T+T+U+V+V+V+W+X+X+X+X+X+X+X+X+@@#@$@. . . @         ",
			"    7.7.X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.V+V+W+X+X+X+X+X+X+X+X+X+X+%@&@*@. . . .             ",
			"    7.7.:+_+(+/+X.X X X X X X X X X X X X X X X X X X X X X X X X X X X 7.7.X+X+X+X+X+X+X+X+X+X+=@-@;@$ . . .                   ",
			"    >@7.7.7.7.7.~+!+)+'+,+>+z.X X X X X X X X X X X X X X X X X X X X X 7.7.X+X+X+X+X+X+X+X+,@'@)@. . . .                       ",
			"            7.7.7.7.7.7.7.7.!@E.D.C.B.A.-.X X X X X X X X X X X X X X X 7.7.X+X+X+X+X+X+~@{@]@. . +                             ",
			"                      7.^@7.7.7.7.7.7.7./@@+++.+ +X.X X X X X X X X X X 7.7.X+X+X+@@#@$@. . . @                                 ",
			"                                  >@7.7.7.7.7.7.7.7.(@_@:@O.<@[@X X X X 7.7.X+%@&@*@. . . .                                     ",
			"                                              7.7.7.7.7.7.7.7.q.p.o.n.m.7.7.}@$ . . y                                           ",
			"                                                        7.^@7.7.7.7.7.7.7.7.. . %                                               ",
			"                                                                    7.7.|@1@                                                    ",
			"                                                                                                                                ",
			"                                                                                                                                "};

			"""

class HelperEdgeManager:
	def __init__(self):
		self.helperEdges = []

	def showEdge(self, edges):
		Wire = Part.Wire(edges)
		edgeName = 'testEdge' + str(len(self.tempGeometry))
		Part.show(Wire, edgeName) 
		FreeCAD.ActiveDocument.recompute()
		self.tempGeometry.append(edgeName)

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
		if len(endPoints) == 2:
			return endPoints
		else:
			return None

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
			
			return face.Edges

		endPoints = self.getEndPoints()
		if not endPoints:
			FreeCAD.Console.PrintError('Pocket Selected? currently not supported')
			return False

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

							tangent = edge.tangentAt(edge.FirstParameter)
							if self.isSamePoint(ep.Point, edge.lastVertex().Point):
								tangent = edge.tangentAt(edge.LastParameter)

							normal = edge.lastVertex().Point.sub(edge.firstVertex().Point)
							if self.isSamePoint(ep.Point, edge.firstVertex().Point):
								normal = edge.firstVertex().Point.sub(edge.lastVertex().Point)

							normal = normal.normalize()

							if Part.Circle == type(edge.Curve):
								normal = self.rotate(tangent, 1.5708)
								endPoint = ep.Point + 5 * normal
								tempEdge = Part.Edge(Part.LineSegment(ep.Point, FreeCAD.Vector(endPoint.x, endPoint.y, endPoint.z)))
								intersectPts = tempEdge.Curve.intersectCC(bbedge.Curve)
							else:
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