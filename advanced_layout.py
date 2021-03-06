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
import os
import logging
from shutil import copyfile
from qgis.core import *
from qgis.PyQt import QtGui
from PyQt5.QtCore import Qt as qt5
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import layout_utils as utils

# Identify environment variable file
env_path = Path('.') / 'qgis_variables.env'
# Load environment variables
load_dotenv(dotenv_path=env_path, override=True)

# dictionary defining polygon style
# for accepted dict key values see https://qgis.org/api/qgsfillsymbollayer_8cpp_source.html#l00160
DEFAULT_POLYGON_STYLE = {'color': '3,190,0,80', 'line_color': 'white', 'width_border': '2.0'}
P_K_INDEX_COLORS = [[1, '#FF0000'],
                    [2, '#FCFC0C'],
                    [3, '#00FF00'],
                    [4, '#0011FF']]  # Red = 1, Yellow = 2, Green = 3, Blue = 4
PH_INDEX_COLORS = [[0, 5.5, '#f00000'],
                   [5.6, 5.9, '#f08000'],
                   [6.0, 6.2, '#e0f000'],
                   [6.3, 6.5, '#80ff00'],
                   [6.6, 6.8, '#00ff80'],
                   [6.9, 7.1, '#40a0ff'],
                   [7.2, 7.4, '#a060ff'],
                   [7.5, 7.6, '#8000ff'],
                   [7.7, 14.0, '#ff00ff']]
DEFAULT_PROJECT_DIR = 'projects/'
Path(DEFAULT_PROJECT_DIR).mkdir(parents=True, exist_ok=True)
JSON_TO_UI_DICT = utils.get_JSON_to_UI()  # dict for converting json fields to UI friendly strings
HECTARE_STRING = 'Area (ha)'
ACRE_STRING = 'Area (ac)'
DEFAULT_CONTENT_SIZE = 9 # mm??
DEFAULT_COL_WIDTH = 45  # mm
MAX_TABLE_HEIGHT = 480  # mm


def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True, type=str,
                        help="path to file containing field polygons (.json)")
    parser.add_argument("-p", "--project_path", required=True, type=str,
                        help="Path to project file. Can be an existing project.")
    parser.add_argument("--farm_name", type=str,
                        help="name of farm to include in layout")
    parser.add_argument("-l", "--layout_name", type=str, default="field layout",
                        help="optional name for layer. useful if creating a new layer in an existing project")
    parser.add_argument("--map_count", type=int, default=1,
                        help="option to create multiple maps within the same layout")
    parser.add_argument("-t", "--table_fields", nargs="+",
                        help="fields to display in table")  # nargs="+" returns a list object
    parser.add_argument("-c", "--color_code", type=str, default=None,
                        help="variable to colour code map")
    parser.add_argument("--label_data", type=str,
                        help="data column to create labels out of")
    parser.add_argument("--area_acres", type=bool,
                        help="display area in acres in table")
    parser.add_argument("--pdf", type=str, help="path to .pdf file to export layout to")
    return parser.parse_args()


"""

    Argument parsing methods
    
"""


def get_table_fields(arguments):
    json_fields = ['name', 'referenceArea_ha']  # default fields always present in table

    if arguments.table_fields is not None:
        for item in arguments.table_fields:
            json_fields.append(item)

    # convert to UI names
    UI_names = []
    for name in json_fields:
        UI_names.append(JSON_TO_UI_DICT[name])

    if arguments.area_acres:
        index = UI_names.index(HECTARE_STRING)
        UI_names.pop(index)
        UI_names.insert(index, ACRE_STRING)

    return UI_names


def get_layer(arguments, proj):
    """
    method to get layer and feature count for that layer
    :param arguments:
    :param proj:
    :return:
    """
    # todo make copy of layer file so that it can be edited and not alter original
    # create layer data file
    original_path = Path(arguments.file)
    layer_data = original_path.parent / Path(original_path.stem + '_qgis_layer' + original_path.suffix)
    copyfile(original_path, layer_data)

    layout_name = "fields"
    if arguments.color_code:
        layout_name = JSON_TO_UI_DICT[arguments.color_code]

    # create layer
    layer = QgsVectorLayer(str(layer_data.resolve()), layout_name, "ogr")

    layer, feature_count = modify_layer(layer, arguments)  # modify based on user args

    if not layer.isValid():
        logging.info("Layer failed to load!")
    else:
        proj.addMapLayer(layer)

    return layer, feature_count


def modify_layer(l, a):
    """
    Method which modifies layer based on user input
     - performs sorting of layer features based on 'name' attribute
     - applies expressions to data
     - rounds float values to 2 decimal places
     - changes headings to UI friendly versions
    :param l:
    :param a: argument namespace
    :return:
    """
    count = 0  # number of features in layer

    with edit(l):

        # UI friendly attribute names
        for field in l.fields():
            field_id = l.fields().indexFromName(field.name())
            l.renameAttribute(field_id, JSON_TO_UI_DICT[field.name()])

        # convert area to acres
        if a.area_acres:
            field_id = l.fields().indexFromName(HECTARE_STRING)
            l.renameAttribute(field_id, ACRE_STRING)

            for feature in l.getFeatures():
                feature.setAttribute(feature.fieldNameIndex(ACRE_STRING), feature[ACRE_STRING]*2.47105)
                l.updateFeature(feature)

        # round to two decimal places all feature attributes that will go into table
        for feature in l.getFeatures():
            count += 1  # iterate count
            for name in get_table_fields(a):
                if isinstance(feature[name], float):  # if a float value round to two decimal places
                    feature.setAttribute(feature.fieldNameIndex(name), round(feature[name], 2))
                    l.updateFeature(feature)

        # sort based on field name

    return l, count


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


def set_polygon_style(l, code=None):
    """
    function which will render colours of polygons based on user input...
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

    elif 'index' in code:  # if an index is used for color coding
        cat_list = []
        for c in P_K_INDEX_COLORS:
            sym = QgsSymbol.defaultSymbol(l.geometryType())
            sym.setColor(QtGui.QColor(c[1]))
            cat = QgsRendererCategory(c[0], sym, str(c[0]))
            cat_list.append(cat)

        renderer = QgsCategorizedSymbolRenderer(code, cat_list)
        l.setRenderer(renderer)
        l.triggerRepaint()

    elif code.startswith('pH'):
        range_list = []
        for c in PH_INDEX_COLORS:
            sym = QgsSymbol.defaultSymbol(l.geometryType())
            sym.setColor(QtGui.QColor(c[2]))
            rng = QgsRendererRange(c[0], c[1], sym, '{0:.1f}-{1:.1f}'.format(c[0], c[1]))
            range_list.append(rng)
        renderer = QgsGraduatedSymbolRenderer(code, range_list)
        l.setRenderer(renderer)
        l.triggerRepaint()

    else:  # otherwise create GraduatedSymbol based on specified colour code variable
        styles = QgsStyle().defaultStyle()
        defaultColorRampNames = styles.colorRampNames()
        ramp = styles.colorRamp(defaultColorRampNames[-6])
        renderer = QgsGraduatedSymbolRenderer()
        renderer.setClassAttribute(code)
        renderer.setSourceColorRamp(ramp)
        # todo allow argument for number of classes
        renderer.updateClasses(l, QgsGraduatedSymbolRenderer.EqualInterval, 10)
        l.setRenderer(renderer)


def set_layer_labels(l, label_data='name'):
    label_settings = QgsPalLayerSettings()
    label_settings.drawLabels = True
    label_settings.fieldName = label_data

    # set up label text format
    text_format = QgsTextFormat()
    text_format.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
    text_format.setSize(50)
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(1.5)
    text_format.setBuffer(buffer)
    shadow = QgsTextShadowSettings()
    shadow.setEnabled(True)
    text_format.setShadow(shadow)
    text_format.setSizeUnit(QgsUnitTypes.RenderPoints)
    label_settings.setFormat(text_format)
    l.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
    l.setLabelsEnabled(True)


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


def get_table_height(n, h_size, c_size):
    """
    Method which gets table height based on font size, and number of features in layer
    returns height in mm
    :param n: number of features in layer
    :param h_size: header font size
    :param c_size: content font size
    :return:
    """
    margin = 1  # num pixels margin
    line_width = 0.5

    size = h_size + (2*margin) + (2*line_width) + (n*(c_size + (2*margin) + line_width))

    return size


def main(args):
    """
    :return:
    """

    # todo: handle creation of qgis project from name instead of full path

    # Initialize QGIS Application
    # QgsApplication.setPrefixPath(os.getenv("QGIS"), True)
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
    tile_layer = QgsRasterLayer(tile_layer_url, '', 'wms')
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

    page_padding = 15
    map_padding = 10

    # Create a layer
    new_layer, num_features = get_layer(args, project)

    color_code = None if args.color_code is None or "" else JSON_TO_UI_DICT[args.color_code]

    # set layer colours
    set_polygon_style(new_layer, color_code)

    # set layer labels
    if args.label_data is not None or "":
        set_layer_labels(new_layer, JSON_TO_UI_DICT[args.label_data])

    """
        Data column
    """
    data_col_width = DEFAULT_COL_WIDTH * (len(get_table_fields(args))) + page_padding

    # order layer features by 'name'
    request = QgsFeatureRequest()

    # set order by field
    clause = QgsFeatureRequest.OrderByClause('to_int(name)', ascending=True)
    orderby = QgsFeatureRequest.OrderBy([clause])
    request.setOrderBy(orderby)

    features = new_layer.getFeatures(request)

    #for feature in features:
    # todo sort layer features by name?
    #   print(feature.attributes())

    # Create a table attached to specific layout
    table = QgsLayoutItemAttributeTable.create(layout)
    table.setVectorLayer(new_layer)  # add layer info to table
    table.setDisplayedFields(get_table_fields(args))
    table.setMaximumNumberOfFeatures(100)
    table.setVerticalGrid(False)  # don't draw vertical lines
    columns = table.columns()
    for column in columns:
        column.setWidth(DEFAULT_COL_WIDTH)  # width in mm
        column.setHAlignment(qt5.AlignHCenter)

    table.setColumns(columns)

    # Create table font
    text_format_heading, text_format_content = utils.get_text_formats(num_features)
    table.setHeaderTextFormat(text_format_heading)
    table.setContentTextFormat(text_format_content)
    # get table height based on layer features and font sizes
    table_height = utils.get_table_height(num_features, text_format_heading.size(), text_format_content.size())
    layout.addMultiFrame(table)

    # Base class for frame items, which form a layout multiframe item.
    frame = QgsLayoutFrame(layout, table)
    frame.setFrameEnabled(True)  # draw frame around outside since vertical grid lines are not drawn
    frame.setFrameStrokeWidth(QgsLayoutMeasurement(0.5, QgsUnitTypes.LayoutMillimeters))
    frame.attemptResize(QgsLayoutSize(table.totalWidth(),
                                      table_height))
    frame.attemptMove(QgsLayoutPoint(page_padding,
                                     page_padding,
                                     QgsUnitTypes.LayoutMillimeters))
    table.addFrame(frame)

    #
    # Legend
    #
    if args.color_code:
        legend = QgsLayoutItemLegend(layout)
        root = QgsLayerTree()

        # don't include ESRI in legend
        for lyr in project.mapLayers().values():
            if lyr.name() != 'ESRI':
                root.addLayer(lyr)

        legend.model().setRootGroup(root)
        layout.addLayoutItem(legend)

        legend.setResizeToContents(False)
        legend.attemptResize(QgsLayoutSize(50, 85))

        legend.setReferencePoint(QgsLayoutItem.UpperLeft)
        legend.attemptMove(QgsLayoutPoint(page_padding,
                                          page_padding + table_height + map_padding,
                                          QgsUnitTypes.LayoutMillimeters))

        if table_height > 400:  # allow more space in table
            legend.attemptMove(QgsLayoutPoint(115, 500, QgsUnitTypes.LayoutMillimeters))

        # legend fonts and icon sizes
        legend.setStyleFont(QgsLegendStyle.Subgroup, text_format_heading.font())
        legend.setStyleFont(QgsLegendStyle.SymbolLabel, text_format_content.font())
        legend.setStyleMargin(QgsLegendStyle.SymbolLabel, 5.0)
        legend.setSymbolHeight(10.0)
        legend.setSymbolWidth(16.0)
        legend.setStyleMargin(QgsLegendStyle.Symbol, 5.0)
        legend.setLineSpacing(5.0)

    # labels at bottom
    now = datetime.now() # current date and time
    date = now.strftime("%d/%m/%Y")
    labels_text = ["farmeye.ie",
                   "Map prepared by Farmeye " + date,
                   "Base layer copyright ESRI"]

    if args.label_data is not None or "":  # text label identifying polygon label variable
        labels_text.append("Label variable: " + JSON_TO_UI_DICT[args.label_data])

    if color_code == 'P index':
        labels_text.append("P index: grass")

    if args.farm_name:
        labels_text.append("Farm: " + args.farm_name)

    n_labels = len(labels_text)
    spacing = 10  # mm?

    for i in range(n_labels):
        label = QgsLayoutItemLabel(layout)
        label.setText(labels_text[i])
        label.setFont(QtGui.QFont("Ariel", 16))
        layout.addLayoutItem(label)
        label.adjustSizeToText()
        label.setReferencePoint(QgsLayoutItem.LowerLeft)
        label.attemptMove(QgsLayoutPoint(page_padding,
                                         page_size.height() - page_padding - (i*spacing),
                                         QgsUnitTypes.LayoutMillimeters))

    """
        Map(s)
    """

    # Create and add the full sized map
    farm_map = QgsLayoutItemMap(layout)
    farm_map.setRect(20, 20, 20, 20)  # DO NOT REMOVE I have no idea what this does, but it is necessary
    farm_map.setExtent(utils.get_rectangle(new_layer, project))  # Set Map Extent
    layout.addLayoutItem(farm_map)
    # resize map, account for data column width
    farm_map.attemptResize(QgsLayoutSize(page_size.width() - data_col_width - (2*page_padding),
                                         page_size.height() - (2*page_padding)))
    farm_map.setReferencePoint(QgsLayoutItem.LowerRight)
    farm_map.attemptMove(QgsLayoutPoint(page_size.width() - page_padding,
                                        page_size.height() - page_padding,
                                        QgsUnitTypes.LayoutMillimeters))

    if args.map_count > 1:  # add the rest of the maps in smaller size
        for c in range(args.map_count - 1):  # -1 since one map already created
            # creating a map based on layout
            farm_map = QgsLayoutItemMap(layout)
            # I have no idea what this does, but it is necessary
            farm_map.setRect(20, 20, 20, 20)
            farm_map.setExtent(utils.get_rectangle(new_layer, project))  # Set Map Extent
            farm_map.setReferencePoint(QgsLayoutItem.LowerRight)
            utils.set_frame(farm_map)  # set frame attributes around map
            layout.addLayoutItem(farm_map)
            farm_map.attemptResize(QgsLayoutSize((page_size.width()-data_col_width) / 2,
                                                  page_size.width() / 2,
                                                  QgsUnitTypes.LayoutMillimeters))
            farm_map.attemptMove(QgsLayoutPoint(page_size.width() - (50 * c),
                                                page_size.height() - (50 * c),
                                                QgsUnitTypes.LayoutMillimeters))

    #
    # scalebar
    #
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setStyle('Single Box')
    scalebar.setUnits(QgsUnitTypes.DistanceMeters)
    scalebar.setNumberOfSegments(4)
    scalebar.setNumberOfSegmentsLeft(0)
    # this will depend on the map extent
    # todo dynamically set units per segment based on map extent?
    scalebar.setUnitsPerSegment(100)
    scalebar.setLinkedMap(farm_map)
    scalebar.setUnitLabel('m')
    scalebar.setMaximumBarWidth(250.0)
    scalebar.setHeight(8)

    # scalebar text format
    # set up label text format
    text_format = QgsTextFormat()
    text_format.setFont(QtGui.QFont("Arial", 36, QtGui.QFont.Bold))
    text_format.setSize(40)
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(1.5)
    text_format.setBuffer(buffer)
    shadow = QgsTextShadowSettings()
    shadow.setEnabled(True)
    text_format.setShadow(shadow)
    text_format.setSizeUnit(QgsUnitTypes.RenderMapUnits)
    scalebar.setTextFormat(text_format)
    scalebar.update()

    # position scalebar
    scalebar.setReferencePoint(QgsLayoutItem.LowerLeft)
    layout.addLayoutItem(scalebar)
    scalebar.attemptMove(QgsLayoutPoint(data_col_width + page_padding + map_padding,
                                        page_size.height() - page_padding - map_padding,
                                        QgsUnitTypes.LayoutMillimeters))

    # north arrow
    arrow_path = os.environ['QGIS'] + "/svg/arrows/NorthArrow_11.svg"
    arrow = QgsLayoutItemPicture(layout)
    arrow.setPicturePath(arrow_path)
    arrow.setReferencePoint(QgsLayoutItem.UpperRight)
    layout.addLayoutItem(arrow)
    arrow.attemptResize(QgsLayoutSize(40, 60, QgsUnitTypes.LayoutMillimeters))
    arrow.attemptMove(QgsLayoutPoint(page_size.width() - page_padding - map_padding,
                                     page_padding + map_padding,
                                     QgsUnitTypes.LayoutMillimeters))

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


