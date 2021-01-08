"""
    Script which generates a QGIS project, custom layout, and a layer based on an input json file

    Note:
        - use forward slashes '/' to specify paths in arguments
        - the path to the QGIS project must exist. however the project file itself doesn't have to exist
        - path to .json file must exist

    ToDo items:
        - create path to QGIS project if it doesn't exist already
        - input name for QGIS project instead of full path (default directory for newly created QGIS projects)
        - create folder with unique name for each run? in folder put qgis project file, copy of file used
            to create layer that can be edited, optional pdf export
        - specify folder name, give option to override existing folder
"""

from qgis.core import *
from qgis.PyQt import QtGui
import os
import logging

# Identify environment variable file
from pathlib import Path
env_path = Path('.') / 'qgis_variables.env'
# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path, override=True)


# dictionary defining polygon style
# for accepted dict key values see https://qgis.org/api/qgsfillsymbollayer_8cpp_source.html#l00160
DEFAULT_POLYGON_STYLE = {'color': '0,0,0,0', 'line_color': 'white', 'width_border': '2.0'}
DEFAULT_PROJECT_DIR = 'projects/'


def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True, type=str,
                        help="path to file containing field polygons (.json)")
    parser.add_argument("-p", "--project_path", required=True, type=str,
                        help="Path to project file. Can be an existing project.")
    parser.add_argument("-l", "--layout_name", type=str, default="field layout",
                        help="optional name for layer. useful if creating a new layer in an existing project")
    parser.add_argument("-t", "--table_fields", nargs="+", default=["name","referenceArea_ha"],
                        help="fields to display in table")  # nargs="+" returns a list object
    parser.add_argument("-c", "--color_code", type=str, default=None,
                        help="variable to colour code map")
    parser.add_argument("--label_data", type=str,
                        help="data column to create labels out of")
    parser.add_argument("--pdf", type=str, help="path to .pdf file to export layout to")
    return parser.parse_args()


def get_layer(arguments, proj):
    # create layer
    layer = QgsVectorLayer(arguments.file, "fields", "ogr")

    # round to two decimal places all feature attribures that will go into table
    # todo round without editing the source file for layer!
    # possibly create a new temp file? or file in same project dir??
    with edit(layer):
        for feature in layer.getFeatures():
            for name in arguments.table_fields:
                if isinstance(feature[name], float):  # if a float value round to two decimal places
                    feature.setAttribute(feature.fieldNameIndex(name), round(feature[name], 2))
                    layer.updateFeature(feature)

    if not layer.isValid():
        logging.info("Layer failed to load!")
    else:
        proj.addMapLayer(layer)

    return layer


def get_layout(name, proj):
    manager = proj.layoutManager()

    # create a new layout
    # todo customise this layout to match Farmeye template?
    layout = QgsPrintLayout(proj)
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


def get_rectangle(l, proj):
    # get layer extents
    ext = l.extent()  # QgsRectangle object
    xmin = ext.xMinimum()  # floats
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()

    r_min = QgsPointXY(xmin, ymin)
    r_max = QgsPointXY(xmax, ymax)

    rect = QgsRectangle(r_min, r_max)

    src_crs = QgsCoordinateReferenceSystem(4326)
    dest_crs = QgsCoordinateReferenceSystem(32629)
    xform = QgsCoordinateTransform(src_crs, dest_crs, proj)
    rect = xform.transform(rect)

    return rect

"""
def round_data(l, dec_places):
    
    round data to a given number of decimal places if it's a double
    :param l:
    :param dec_places:
    :return:
    

    # set expression to round table items to 2 decimal places
    expressions = []
    for name in args.table_fields:
        # create an expression for each field specified in arguments
        exp = QgsExpression('round(' + name + ', 2)')
        expressions.append(exp)
        
    """


def set_polygon_style(l, code=None):
    """
    function which will render colours of polygons based on user input...
    todo: if no colour coding specified, apply default white polygon boundaries and no fill
    todo: implement various colour coding schemes for different mineral types
        - create another utilities file for rendering layers based on Farmeye-specific use cases
    :param l: a layer
    :param code: variable to base colour coding on
    :return:
    """

    if code is None or "":  # if no colour code set, use default style
        style = DEFAULT_POLYGON_STYLE
        symbol = QgsFillSymbol.createSimple(style)
        # create renderer to colour polygons in layer
        l.renderer().setSymbol(symbol)
        l.triggerRepaint()
    else:  # otherwise create GraduatedSymbol based on specified colour code variable
        styles = QgsStyle().defaultStyle()
        defaultColorRampNames = styles.colorRampNames()
        ramp = styles.colorRamp(defaultColorRampNames[-3])
        renderer = QgsGraduatedSymbolRenderer()
        renderer.setClassAttribute(code)
        renderer.setSourceColorRamp(ramp)
        # todo allow argument for number of classes (set to 10 here)
        renderer.updateClasses(l, QgsGraduatedSymbolRenderer.EqualInterval, 10)
        l.setRenderer(renderer)


def set_layer_labels(l, label_data):
    label_settings = QgsPalLayerSettings()
    label_settings.drawLabels = True
    label_settings.fieldName = label_data

    # set up label text format
    text_format = QgsTextFormat()
    text_format.setFont(QtGui.QFont("Arial", 10))
    text_format.setSize(50)
    text_format.setSizeUnit(QgsUnitTypes.RenderMapUnits)
    label_settings.setFormat(text_format)
    l.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
    l.setLabelsEnabled(True)
    #l.triggerRepaint()


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


def set_frame(layout_item):
    """
    Method which sets the frame settings for any QgsLayoutItem
    :param layout_item: an object which extends QgsLayoutItem (e.g. QgsLayoutItemMap)
    :return:
    """

    layout_item.setFrameEnabled(True)
    layout_item.setFrameStrokeColor(QtGui.QColor(18, 101, 135, 255))
    layout_item.setFrameStrokeWidth(QgsLayoutMeasurement(5.0, QgsUnitTypes.LayoutMillimeters))


def get_project_path(input_string):
    """

    :param input_string:
    :return:
    """

    input_path = Path(input_string)
    project_path = ''

    # if input_string is a path to .qgs file, return input_string
    if input_path.suffix == '.qgs':
        project_path = input_path

    # if input_string is a path to a dir, return path to .qgs file in that dir
    elif input_path.is_dir():
        project_path = input_path / 'project.qgs'

    # if input_string is only a name, return path to 'name'.qgs in default project dir
    elif input_path.suffix == '':
        project_path = DEFAULT_PROJECT_DIR / input_path.with_suffix('.qgs')

    else:
        logging.info("invalid project name/file specified. Most likely a non .qgs file specified")

    return project_path


def main(args):
    """
    :return:
    """

    # todo: handle creation of qgis project from name instead of full path


    # Initialize QGIS Application
    QgsApplication.setPrefixPath(os.getenv("QGIS"), True)
    app = QgsApplication([], False, None)
    QgsApplication.initQgis()

    # need to remove old layers and layouts from QgsProject.instance() because using
    # QgsApplication.exitQgis() doesn't work when called from GUI

    # remove old layers
    registryLayers = QgsProject.instance().mapLayers().keys()
    layersToRemove = set(registryLayers)
    QgsProject.instance().removeMapLayers(list(layersToRemove))

    # remove old layouts
    layout_manager = QgsProject.instance().layoutManager()
    layouts_list = layout_manager.printLayouts()
    for l in layouts_list:
        layout_manager.removeLayout(l)

    # project is 'cleared' now
    project = QgsProject.instance()
    proj_path = str(get_project_path(args.project_path))
    project.setFileName(proj_path)  # set project name
    crs = QgsCoordinateReferenceSystem()
    crs.createFromString("EPSG:32629")
    project.setCrs(crs)

    # add tile layer
    tile_layer_url = 'type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    tile_layer = QgsRasterLayer(tile_layer_url, 'ESRI', 'wms')
    # tile_layer.setCrs(crs)

    if tile_layer.isValid():
        project.addMapLayer(tile_layer)
    else:
        logging.info('invalid layer')

    # Create layout
    layout = get_layout(args.layout_name, project)

    # get layout extents/size?
    # returns a QgsLayoutSize object
    # QgsPrintLayout(QgsLayout) -> QgsLayoutPageCollection -> QgsLayoutItemPage -> QgsLayoutSize
    page_size = layout.pageCollection().pages()[0].pageSize()

    # Create a layer
    new_layer = get_layer(args, project)

    # set layer colours
    set_polygon_style(new_layer, args.color_code)

    # set layer labels
    if args.label_data is not None or "":
        set_layer_labels(new_layer, args.label_data)

    # creating a map based on layout
    map = QgsLayoutItemMap(layout)
    # I have no idea what this does, but it is necessary
    map.setRect(20, 20, 20, 20)
    map.setExtent(get_rectangle(new_layer, project))  # Set Map Extent
    set_frame(map)  # set frame attributes around map
    layout.addLayoutItem(map)
    map.attemptResize(page_size)  # resize map to layout size

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
    set_frame(frame)  # set frame attributes around table. don't confuse with Frame objects, maybe should rename..
    # todo dynamically resize frame to match table size?
    # s = QgsLayoutSize()
    # s.setHeight(table.totalHeight())
    # s.setWidth(table.totalWidth())
    frame.attemptResize(page_size, True)
    table.addFrame(frame)
    # table.recalculateFrameSizes()

    # add scalebar
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setStyle('Single Box')
    scalebar.setUnits(QgsUnitTypes.DistanceMeters)
    scalebar.setNumberOfSegments(4)
    scalebar.setNumberOfSegmentsLeft(0)
    # this will depend on the map extent
    # todo dynamically set units per segment based on map extent?
    scalebar.setUnitsPerSegment(100)
    scalebar.setLinkedMap(map)
    scalebar.setUnitLabel('m')
    scalebar.setFont(QtGui.QFont('Arial', 36))
    scalebar.setMaximumBarWidth(250.0)
    scalebar.setHeight(8)
    scalebar.update()
    layout.addLayoutItem(scalebar)
    scalebar.attemptMove(QgsLayoutPoint(575, 550, QgsUnitTypes.LayoutMillimeters))

    # add farmeye logo in bottom right corner
    logo_path = 'images/logo.png'

    logo = QgsLayoutItemPicture(layout)
    logo.setPicturePath(logo_path)
    layout.addLayoutItem(logo)
    logo.attemptMove(QgsLayoutPoint(580, 370, QgsUnitTypes.LayoutMillimeters))
    logo.attemptResize(QgsLayoutSize(250, 150, QgsUnitTypes.LayoutMillimeters))
    set_frame(logo)

    # this creates a QgsLayoutExporter object
    exporter = QgsLayoutExporter(layout)

    # export to pdf if required
    if args.pdf is not None:
        pdf_path = Path(args.pdf)
        exporter.exportToPdf(pdf_path, QgsLayoutExporter.PdfExportSettings())

    # save the project
    project.write()


if __name__ == "__main__":
    arguments = get_args()

    main(arguments)


