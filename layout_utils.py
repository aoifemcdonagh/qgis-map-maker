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
    # l.triggerRepaint()


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

