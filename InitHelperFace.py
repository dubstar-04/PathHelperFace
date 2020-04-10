
import FreeCADGui
from PySide import QtGui
import PathHelperFaceGui, PathHelperFace
import os

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Icons' )

def getIcon(iconName):
     return os.path.join( iconPath , iconName)

def updateMenu(workbench):
    print('Workbench loaded:', workbench)

    if workbench == 'PathWorkbench':
        print('load the helper menu')
        mw = FreeCADGui.getMainWindow()
        menu = mw.findChildren(QtGui.QMenu, "Supplemental Commands")[0]
        action = QtGui.QAction(menu)
        action.setText("Helper Face")
        action.setIcon(QtGui.QPixmap(getIcon('Path_HelperFace.svg')))
        #action.setObjectName("Path")
        action.setStatusTip("Create a helper face")
        action.triggered.connect(PathHelperFaceGui.Show)
        menu.addAction(action)

FreeCADGui.getMainWindow().workbenchActivated.connect(updateMenu)