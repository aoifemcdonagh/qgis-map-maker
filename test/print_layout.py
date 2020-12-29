from qgis.PyQt import QtGui
from qgis.core import *
from qgis.gui import *
from qgis.utils import *

import os

# Identify environment variable file
from pathlib import Path
env_path = Path('.') / 'qgis_variables.env'
# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path, override=True)

# setup project
project_path = "C:\\Users\\Aoife\\Documents\\farmeye\\qgis project\\test_project.qgs"

# Initialize QGIS Application
QgsApplication.setPrefixPath(os.getenv("QGIS"), True)
app = QgsApplication([], True)
app.initQgis()
QgsProject.instance().setFileName(project_path)
print(QgsProject.instance().fileName())

# get layer
new_layer = QgsVectorLayer("C:\\Users\\Aoife\\Documents\\farmeye\\qgis project\\joe_nolan.json", "test_joe_nolan","ogr")

"""
# set correct CRS 
crs = new_layer.crs()
crs.createFromString("EPSG:4326")
new_layer.setCrs(crs)"""

# get layer extents
ext = new_layer.extent()
xmin = ext.xMinimum()
xmax = ext.xMaximum()
ymin = ext.yMinimum()
ymax = ext.yMaximum()

""" Layout setup """

project = QgsProject.instance()
manager = project.layoutManager()
layoutName = 'test layout'
layouts_list = manager.printLayouts()
# remove any duplicate layouts
for layout in layouts_list:
    if layout.name() == layoutName:
        manager.removeLayout(layout)
layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName(layoutName)
manager.addLayout(layout)

# create map item in the layout
map = QgsLayoutItemMap(layout)
#map.setRect(20, 20, 20, 20)

map.setExtent(QgsRectangle(xmin,ymin,xmax,ymax))
map.setBackgroundColor(QtGui.QColor(255, 255, 255, 0))
layout.addLayoutItem(map)

# set the map extent
ms = QgsMapSettings()
ms.setLayers([new_layer])  # set layers to be mapped
#rect = QgsRectangle(ms.fullExtent())
#rect.scale(1.0)
#ms.setExtent(rect)
#map.setExtent(rect)

#map.attemptMove(QgsLayoutPoint(5, 20, QgsUnitTypes.LayoutMillimeters))
#map.attemptResize(QgsLayoutSize(180, 180, QgsUnitTypes.LayoutMillimeters))
"""
legend = QgsLayoutItemLegend(layout)
legend.setTitle("Legend")
layerTree = QgsLayerTree()
layerTree.addLayer(new_layer)
legend.model().setRootGroup(layerTree)
layout.addLayoutItem(legend)
legend.attemptMove(QgsLayoutPoint(230, 15, QgsUnitTypes.LayoutMillimeters))


scalebar = QgsLayoutItemScaleBar(layout)
scalebar.setStyle('Line Ticks Up')
scalebar.setUnits(QgsUnitTypes.DistanceMeters)
scalebar.setNumberOfSegments(4)
scalebar.setNumberOfSegmentsLeft(0)
scalebar.setUnitsPerSegment(0.5)
scalebar.setLinkedMap(map)
scalebar.setUnitLabel('m')
scalebar.setFont(QtGui.QFont('Arial', 14))
scalebar.setMaximumBarWidth(250.0)
scalebar.update()
layout.addLayoutItem(scalebar)
scalebar.attemptMove(QgsLayoutPoint(220, 190, QgsUnitTypes.LayoutMillimeters))

title = QgsLayoutItemLabel(layout)
title.setText("My Title")
title.setFont(QtGui.QFont('Arial', 24))
title.adjustSizeToText()
layout.addLayoutItem(title)
#title.attemptMove(QgsLayoutPoint(10, 5, QgsUnitTypes.LayoutMillimeters))
"""
layout = manager.layoutByName(layoutName)
layout.addLayoutItem(map)
exporter = QgsLayoutExporter(layout)

fn = 'C:\\Users\\Aoife\\Documents\\farmeye\\qgis project\\layout_export.pdf'
# exporter.exportToImage(fn, QgsLayoutExporter.ImageExportSettings())
exporter.exportToPdf(fn, QgsLayoutExporter.PdfExportSettings())

# add layer to project
project.addMapLayer(new_layer)

# save the project
project.write()
