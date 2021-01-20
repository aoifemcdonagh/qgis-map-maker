"""
    collection of utility methods for creating QGIS layout data, objects, etc...
"""
import os
import logging
from qgis.core import *
from qgis.PyQt import QtGui
from pathlib import Path

# dictionary defining polygon style
# for accepted dict key values see https://qgis.org/api/qgsfillsymbollayer_8cpp_source.html#l00160
DEFAULT_POLYGON_STYLE = {'color': '0,0,0,0', 'line_color': 'white', 'width_border': '2.0'}
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
DEFAULT_ATTRIBUTE_NAMES = 'attribute_names.txt'

HECTARE_STRING = 'Area (ha)'
ACRE_STRING = 'Area (ac)'
DEFAULT_CONTENT_SIZE = 9 # mm??
DEFAULT_COL_WIDTH = 45  # mm
MAX_TABLE_HEIGHT = 480  # mm

"""

    Argument parsing methods

"""


def get_table_fields(arguments):
    json_dict = get_JSON_to_UI()
    json_fields = ['name', 'referenceArea_ha']  # default fields always present in table

    if arguments.table_fields is not None:
        for item in arguments.table_fields:
            json_fields.append(item)

    # convert to UI names
    UI_names = []
    for name in json_fields:
        UI_names.append(json_dict[name])

    if arguments.area_acres:
        index = UI_names.index(HECTARE_STRING)
        UI_names.pop(index)
        UI_names.insert(index, ACRE_STRING)

    return UI_names


def get_UI_to_JSON(file=DEFAULT_ATTRIBUTE_NAMES):
    """
    Method that returns a dictionary with keys: json field name, values: UI-suitable translation
    :return:
    """
    names = {}

    with open(file, 'r') as data:
        lines = data.read().splitlines()

        for line in lines:
            array = line.split(",")
            names[array[1]] = array[0]

    return names


def get_JSON_to_UI(file=DEFAULT_ATTRIBUTE_NAMES):
    """
    Method that returns a dictionary with keys: json field name, values: UI-suitable translation
    :return:
    """
    names = {}

    with open(file, 'r') as data:
        lines = data.read().splitlines()

        for line in lines:
            array = line.split(",")
            names[array[0]] = array[1]

    return names


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
    json_dict = get_JSON_to_UI()
    count = 0  # number of features in layer

    with edit(l):

        # UI friendly attribute names
        for field in l.fields():
            field_id = l.fields().indexFromName(field.name())
            l.renameAttribute(field_id, json_dict[field.name()])

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

    elif code.startswith('index'):  # if an index is used for color coding
        cat_list = []
        for c in P_K_INDEX_COLORS:
            sym = QgsSymbol.defaultSymbol(l.geometryType())
            sym.setColor(QtGui.QColor(c[1]))
            cat = QgsRendererCategory(c[0], sym, str(c[0]))
            cat_list.append(cat)

        renderer = QgsCategorizedSymbolRenderer(code, cat_list)
        l.setRenderer(renderer)
        l.triggerRepaint()

    elif 'index' in code:  # if an index is used for color coding
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


def set_frame(layout_item):
    """
    Method which sets the frame settings for any QgsLayoutItem
    :param layout_item: an object which extends QgsLayoutItem (e.g. QgsLayoutItemMap)
    :return:
    """

    layout_item.setFrameEnabled(True)
    layout_item.setFrameStrokeColor(QtGui.QColor(18, 101, 135, 255))
    layout_item.setFrameStrokeWidth(QgsLayoutMeasurement(5.0, QgsUnitTypes.LayoutMillimeters))



def get_fonts():
    """
    Function which returns fonts QtGui.QFont objects
    todo optionally base fonts on layout size
    :return:
    """

    content = QtGui.QFont()
    header = QtGui.QFont()
    content.setPointSize(30)
    header.setPointSize(32)

    return [content, header]


def get_text_formats(n_features):
    """
    Method which generates QgsTextFormat objects for headings and content in table
    size is in points
    :return:
    """

    content_size = calculate_font_size(n_features)
    heading_size = content_size + 1

    heading_format = QgsTextFormat()
    heading_format.setFont(QtGui.QFont("Arial", 32))
    heading_format.setSize(heading_size)
    heading_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

    content_format = QgsTextFormat()
    content_format.setFont(QtGui.QFont("Arial", 30))
    content_format.setSize(content_size)
    content_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

    return heading_format, content_format


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


def calculate_font_size(n_features, size=DEFAULT_CONTENT_SIZE):
    """
    calculate the appropriate content font size based on number of features in layer
    :param n_features:
    :param size:
    :return: size of content font to be used
    """

    # if table with current font size is too large, decrease font size and check again
    if get_table_height(n_features, size + 1, size) > MAX_TABLE_HEIGHT:
        # recursive search for font size that doesn't exceed max table height
        size = calculate_font_size(n_features, size - 1)

    return size


def get_table_height(n, h_size, c_size):
    """
    Method which gets table height based on font size, and number of features in layer
    returns height in mm
    :param n: number of features in layer
    :param h_size: header font size
    :param c_size: content font size
    :return:
    """
    margin = 0.75  # num pixels margin
    line_width = 0.5

    size = h_size + (2*margin) + (2*line_width) + (n*(c_size + (2*margin) + line_width))

    return size
