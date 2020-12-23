"""
    Script which generates a QGIS project, custom layout, and a layer based on an input json file

    Note:
        - use forward slashes '/' to specify paths in arguments
        - the path to the QGIS project must exist. however the project file itself doesn't have to exist
        - path to .json file must exist

    ToDo items:
        - create path to QGIS project if it doesn't exist already
        - input name for QGIS project instead of full path (default directory for newly created QGIS projects)

"""

from qgis.core import *
from qgis.PyQt import QtGui
import PyQt5 as qt
import os

# Identify environment variable file
from pathlib import Path
env_path = Path('.') / 'qgis_variables.env'
# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path, override=True)


def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True, type=str,
                        help="path to file containing field polygons (.json)")
    parser.add_argument("-p", "--project_path", required=True, type=str,
                        help="Path to project file. Can be an existing project.")
    parser.add_argument("-l", "--layout_name", type=str, default="field layout",
                        help="optional name for layer. useful if creating a new layer in an existing project")
    parser.add_argument("--table_fields", nargs="+", default=["name","referenceArea_ha"],
                        help="fields to display in table")  # nargs="+" returns a list object
    parser.add_argument("--pdf", type=str, help="path to .pdf file to export layout to")
    return parser.parse_args()


def get_layer(name, proj):
    # create layer
    layer = QgsVectorLayer(name, "fields", "ogr")
    crs = layer.crs()
    crs.createFromId(4326)  # WGS84 - EPSG4326 , IRENET95 - EPSG2158
    layer.setCrs(crs)

    if not layer.isValid():
        print("Layer failed to load!")
    else:
        proj.addMapLayer(layer)

    return layer


def get_fonts():
    """
    Function which returns fonts QtGui.QFont objects
    todo optionally base fonts on layout size
    :return:
    """

    content = QtGui.QFont()
    header = QtGui.QFont()
    content.setPointSize(36)
    header.setPointSize(40)

    return [content, header]


def get_layout(name, proj):
    manager = proj.layoutManager()

    # create a new layout
    # todo customise this layout to match Farmeye template?
    layout = QgsPrintLayout(project)
    layoutName = name

    # remove duplicate layouts
    layouts_list = manager.printLayouts()
    for l in layouts_list:
        if l.name() == layoutName:
            manager.removeLayout(l)

    # initializes default settings for blank print layout canvas
    layout.initializeDefaults()

    # set layout size
    pc = layout.pageCollection()
    pc.pages()[0].setPageSize('A1', QgsLayoutItemPage.Orientation.Landscape)

    layout.setName(layoutName)
    manager.addLayout(layout)

    return layout


if __name__ == "__main__":
    args = get_args()

    # todo: handle creation of qgis project from name instead of full path

    # Initialize QGIS Application
    QgsApplication.setPrefixPath(os.getenv("QGIS"), True)
    app = QgsApplication([], True)
    app.initQgis()
    project = QgsProject.instance()
    project.setFileName(args.project_path)  # set project name

    # Create layout
    layout = get_layout(args.layout_name, project)

    # get layout extents/size?
    # returns a QgsLayoutSize object
    # QgsPrintLayout(QgsLayout) -> QgsLayoutPageCollection -> QgsLayoutItemPage -> QgsLayoutSize
    page_size = layout.pageCollection().pages()[0].pageSize()

    # Create a layer
    new_layer = get_layer(args.file, project)
    # get layer extents
    ext = new_layer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()

    # adding map to layout
    map = QgsLayoutItemMap(layout)
    # I have no idea what this does, but it is necessary
    map.setRect(20, 20, 20, 20)
    # Set Map Extent
    # defines map extent using map coordinates
    rectangle = QgsRectangle(xmin, ymin, xmax, ymax)
    map.setExtent(rectangle)
    map.setBackgroundColor(QtGui.QColor(0, 255, 0, 100))
    layout.addLayoutItem(map)

    # Create a table attached to specific layout
    table = QgsLayoutItemAttributeTable.create(layout)
    table.setVectorLayer(new_layer)  # add layer info to table
    table.setDisplayedFields(args.table_fields)

    # Create table font
    content_font, header_font = get_fonts()
    table.setContentFont(content_font)
    table.setHeaderFont(header_font)
    layout.addMultiFrame(table)

    # Base class for frame items, which form a layout multiframe item.
    frame = QgsLayoutFrame(layout, table)
    # todo dynamically resize frame to match table size?
    frame.attemptResize(page_size, False)
    table.addFrame(frame)

    # todo change map move and resize
    # Move & Resize map on print layout canvas
    #map.attemptMove(QgsLayoutPoint(30, 0, QgsUnitTypes.LayoutMillimeters))
    # resize map to layout size
    map.attemptResize(page_size)

    # todo resize map to layout size (since layout and layer size differ)

    # this creates a QgsLayoutExporter object
    exporter = QgsLayoutExporter(layout)

    # export to pdf if required
    if args.pdf is not None:
        pdf_path = Path(args.pdf)
        exporter.exportToPdf(pdf_path, QgsLayoutExporter.PdfExportSettings())

    # save the project
    project.write()
