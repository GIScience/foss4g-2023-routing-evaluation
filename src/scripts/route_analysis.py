#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compare and evaluate Google vs ORS routes"""
import argparse
import os
import sys
import json
import logging
import geopandas as gpd
from pathlib import Path

# change to the working directory to the python file location so that the imports work
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from route_analyst.responses import ORSDirectionsResponse
from route_analyst.routes import GoogleRoute


def extract_info(data_dir, out_dir, city):
    """
    Extracts information about route objects and writes to them file
    :return: a csv and geojson file with all data
    """

    logger = logging.getLogger(__file__)
    logging.basicConfig(level=logging.INFO)

    data_dir = Path(data_dir)
    out_dir = data_dir / city / out_dir
    out_dir.mkdir(exist_ok=True)

    google_routes_dir = data_dir / city / "google_routes"
    google_routes_file = (
        google_routes_dir / f"{city}_50_routes_per_hour.geojson"
    )  # 50 routes
    all_google_routes = gpd.read_file(google_routes_file)
    all_google_routes["hour"] = all_google_routes.id.apply(
        lambda x: x[1:].split("_")[0]
    )

    ors_type_list = [
        "normal",
        "modelled_mean",
        "modelled_p50",
        "modelled_p85",
        "uber_p85",
    ]

    routes_list_full = []
    routes_id_list = [None]  # create a value to compare to

    for index, google_route in all_google_routes.iterrows():
        logger.info(f"Processing route number {google_route.id}")
        # Google Route
        if google_route.id in routes_id_list:
            alternative_id += 1
        else:
            alternative_id = 0
            routes_id_list.append(google_route.id)
        google_route.id = f"{google_route.id}_{alternative_id}"
        google_route_obj = GoogleRoute(google_route)

        # ORS Route
        for ors_type in ors_type_list:
            item = (
                data_dir
                / city
                / f"ors_routes_{ors_type}"
                / f"route_{ors_type}_{google_route.hour}_{google_route.id}.geojson"
            )
            if os.path.isfile(item):
                with open(item) as f:
                    data = json.load(f)
                    ors_route_obj = ORSDirectionsResponse(data).routes[0]
                    dur_diff_sec = ors_route_obj.duration_diff_sec(google_route)
                    dur_diff_perc = ors_route_obj.duration_diff_perc(google_route)
                    dist_diff_meter = ors_route_obj.distance_diff_meter(google_route)
                    dist_diff_perc = ors_route_obj.distance_diff_perc(google_route)
                    geom_diff_perc = ors_route_obj.geometry_diff_perc(google_route)
                    geom_diff_hausdorff = ors_route_obj.geometry_diff_hausdorff(
                        google_route
                    )

                routes_list_full.append(
                    {
                        "route_id": google_route.id,
                        "ors_route": str(item),
                        "ors_type": ors_type,
                        "hour": google_route.hour,
                        "google_distance": round(google_route_obj.distance, 2),
                        "ors_distance": round(ors_route_obj.distance, 2),
                        "google_dur_in_traffic_sec": round(
                            google_route_obj.duration_in_traffic, 2
                        ),
                        "google_dur_sec": round(google_route_obj.duration, 2),
                        "ors_dur_sec": round(ors_route_obj.duration, 2),
                        "duration_diff_sec": round(dur_diff_sec, 2),
                        "duration_diff_perc": round(dur_diff_perc, 2),
                        "google_dist_meter": round(google_route_obj.distance, 2),
                        "ors_dist_meter": round(ors_route_obj.distance, 2),
                        "distance_diff_meter": round(dist_diff_meter, 2),
                        "distance_diff_perc": round(dist_diff_perc, 2),
                        "geometry_diff_perc": round(geom_diff_perc, 4),
                        "geometry_diff_hausdorff": round(geom_diff_hausdorff, 5),
                        # "geom_ors": ors_route_obj.geometry,
                        "geometry": google_route_obj.geometry,
                    }
                )
            else:
                logger.info(f"Route {item} doesn't exist.")
                continue

    # export GeoDataFrame with all routes to file
    logger.info("Generating merged Geodataframe...")
    gdf_full = gpd.GeoDataFrame(routes_list_full)
    gdf_full.set_geometry(col="geometry", inplace=True)
    gdf_full.to_file(out_dir / f"{city}_results_full.geojson")
    gdf_full.to_csv(out_dir / f"{city}_results_full.csv")

    return len(routes_list_full)  # for testing


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyzes routes and calculates statistics"
    )
    parser.add_argument(
        "-c",
        required=True,
        dest="city",
        metavar="City name",
        type=str,
        help="City name. Check Readme for more information.",
    )
    args = parser.parse_args()

    data_dir = "data"
    out_dir = "export"

    extract_info(data_dir=data_dir, out_dir=out_dir, city=args.city)
