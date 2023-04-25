import random
from shapely.geometry import Point


def get_random_coordinates(bbox=None, polygon=None):
    """
    Create random start and end points to generate random route requests
    :param
    bbox: list containing xmin, ymin, xmax, ymax of bounding box
    polygon: list of lists containing the coordinates of the polygon
    :return:
    """
    if bbox:
        xmin, ymin, xmax, ymax = bbox
        start_lon = random.uniform(xmin, xmax)
        end_lon = random.uniform(xmin, xmax)
        start_lat = random.uniform(ymin, ymax)
        end_lat = random.uniform(ymin, ymax)
    elif polygon:
        xmin, ymin, xmax, ymax = polygon.bounds
        start_lon = random.uniform(xmin, xmax)
        start_lat = random.uniform(ymin, ymax)
        while not Point(float(start_lon), float(start_lat)).within(polygon):
            start_lon = random.uniform(xmin, xmax)
            start_lat = random.uniform(ymin, ymax)
        end_lat = random.uniform(ymin, ymax)
        end_lon = random.uniform(xmin, xmax)
        while not Point(float(end_lon), float(end_lat)).within(polygon):
            end_lat = random.uniform(ymin, ymax)
            end_lon = random.uniform(xmin, xmax)
    else:
        raise ValueError("Either bbox or polygon must be given.")
    return [[start_lon, start_lat], [end_lon, end_lat]]
