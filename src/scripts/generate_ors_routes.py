#!/usr/bin/env python
# coding: utf-8
"""Generate ORS route for each Google Route"""

from pathlib import Path
import geopandas as gpd
import numpy as np
from datetime import datetime
import logging
import sys
import argparse

# change to the working directory to the python file location so that the imports work
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from route_analyst import ORSRoutingClient


ORS_INSTANCES = {
    "normal": "http://localhost:8080/ors/",  # ors without traffic data
    "modelled_mean": "http://localhost:8081/ors/",  # ors with modelled mean traffic speed
    "modelled_p50": "http://localhost:8082/ors/",  # ors with modelled 50th percentile traffic speed
    "modelled_p85": "http://localhost:8083/ors/",  # ors with modelled 85th percentile traffic speed
    "uber_p85": "http://localhost:8084/ors/",  # ors with uber 85th percentile traffic speed
}
PROFILE = "driving-car"
FORMAT = "geojson"

logger = logging.getLogger(__file__)
logging.basicConfig(level=logging.INFO)


def split_line(splits, google_geom):
    """
    Splits the geometry in evenly spaced subpoints (splits) and returns the coordinates
    :return: list with coordinates
    """
    route_coordinates = []
    distances = np.linspace(0, google_geom.length, splits)
    points = [google_geom.interpolate(distance) for distance in distances]
    for i in range(0, len(points)):
        route_coordinates.append((points[i].x, points[i].y))
    return route_coordinates


def main(data_dir, ors_type, city, splits):
    """
    Reads Google routes and generates similar ORS routes
    :return: a geojson file for each route
    """
    # Get ors url
    ors_url = ORS_INSTANCES[ors_type]
    data_dir = Path(data_dir)

    # ORS query parameters
    body = {
        "coordinates": None,
        "instructions": "false",
        "preference": "fastest",
        "departure": None,
        # "alternative_routes": {"share_factor": 0.8, "target_count": 2}
    }

    # Get directories and create output directory
    google_routes_dir = data_dir / city / "google_routes"
    ors_routes_dir = data_dir / city / f"ors_routes_{ors_type}"
    ors_routes_dir.mkdir(exist_ok=True)

    # Read google routes
    google_routes_file = (
        google_routes_dir / f"{city}_50_routes_per_hour.geojson"
    )  # 50 routes
    all_google_routes = gpd.read_file(google_routes_file)
    all_google_routes["hour"] = all_google_routes.id.apply(
        lambda x: x[1:].split("_")[0]
    )

    # Client to query ORS
    ors_client = ORSRoutingClient(base_url=ors_url)

    routes_id_list = [0]
    alternative_id = 0

    for index, google_route in all_google_routes.iterrows():
        logger.info(f"Processing route number {google_route.id} - {alternative_id}")

        if google_route.id in routes_id_list:
            alternative_id += 1
        else:
            alternative_id = 0
            routes_id_list.append(google_route.id)
        google_route.id = f"{google_route.id}_{alternative_id}"  # check if the id was used before and skip it (no alternative routes)

        google_geom = google_route.geometry
        google_departure = datetime.isoformat(google_route.departure_time)

        # Extract coordinates from google route to be passed to ORS
        route_coordinates = split_line(splits, google_geom)

        # Calculate ORS routes
        body["coordinates"] = route_coordinates
        body["departure"] = google_departure
        try:
            response_normal = ors_client.request(
                params=body, profile=PROFILE, format=FORMAT
            )
            response_normal.to_file(
                ors_routes_dir
                / f"route_{ors_type}_{google_route.hour}_{google_route.id}.geojson"
            )
        except Exception as e:
            logger.warning(f"Could not process route {google_route.id}:")
            logger.warning(e)
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ORS routes")
    parser.add_argument(
        "-t",
        required=True,
        dest="ors_type",
        metavar="ORS type",
        type=str,
        help="Type of ORS. Check Readme for more information.",
    )
    parser.add_argument(
        "-c",
        required=True,
        dest="city",
        metavar="City name",
        type=str,
        help="City name. Check Readme for more information.",
    )
    parser.add_argument(
        "-s",
        required=False,
        dest="splits",
        metavar="LineString splits",
        type=int,
        default=10,
        help="Route splits, default = 10",
    )
    args = parser.parse_args()

    data_dir = "data"

    main(data_dir, ors_type=args.ors_type, city=args.city, splits=args.splits)
