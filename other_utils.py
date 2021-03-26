from qgis.core import *

INDEX_VALS = [" P1", " P2", " P3", " P4", " K1", " K2", " K3", " K4"]


def remove_index(file):
    # create layer
    layer = QgsVectorLayer(file, "fields", "ogr")

    with edit(layer):
        for feature in layer.getFeatures():
            name = feature["name"]
            for index in INDEX_VALS:
                if index in name:
                    feature.setAttribute(feature.fieldNameIndex("name"),
                                         feature["name"].replace(index, ""))
                    layer.updateFeature(feature)


def remove_no_sample(file):
    """
    remove layer feature if no soil sample present
    :param file:
    :return:
    """
    # create layer
    layer = QgsVectorLayer(file, "fields", "ogr")

    with edit(layer):
        for feature in layer.getFeatures():
            date = feature["soilTest_date"]
            if date is NULL:
                layer.deleteFeature(feature.id)
                layer.updateFeature(feature)
