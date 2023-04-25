#!/usr/bin/env python
# coding: utf-8
# Generate random Google Routes

import argparse
import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
import os
import sys
import random
from tqdm import tqdm
import dotenv
from pathlib import Path

# change to the working directory to the python file location so that the imports work
sys.path.append(str(Path(__file__).parent.parent.resolve()))
dotenv.load_dotenv("../.env")

from route_analyst import routingpy, utils, GoogleRoute
from route_analyst.routingpy.exceptions import (
    RouterApiError,
    RouterServerError,
    OverQueryLimit,
)

random.seed(123)

STATUS_CODES = {
    "NOT_FOUND": {
        "code": 404,
        "message": "At least one of the locations specified in the request's origin, destination, or waypoints could not be geocoded.",
    },
    "ZERO_RESULTS": {
        "code": 404,
        "message": "No route could be found between the origin and destination.",
    },
    "MAX_WAYPOINTS_EXCEEDED": {
        "code": 413,
        "message": "Too many waypoints were provided in the request. The maximum is 25 excluding the origin and destination points.",
    },
    "MAX_ROUTE_LENGTH_EXCEEDED": {
        "code": 413,
        "message": "The requested route is too long and cannot be processed.",
    },
    "INVALID_REQUEST": {
        "code": 400,
        "message": "The provided request is invalid. Please check your parameters or parameter values.",
    },
    "OVER_DAILY_LIMIT": {
        "code": 429,
        "message": "This may be caused by an invalid API key, or billing issues.",
    },
    "OVER_QUERY_LIMIT": {
        "code": 429,
        "message": "The service has received too many requests from your application within the allowed time period.",
    },
    "REQUEST_DENIED": {
        "code": 403,
        "message": "The service denied use of the directions service by your application.",
    },
    "UNKNOWN_ERROR": {
        "code": 503,
        "message": "The directions request could not be processed due to a server error. The request may succeed if you try again.",
    },
}


def _parse_direction_json(response, alternatives):
    """

    :param response:
    :param alternatives:
    :return:
    """
    if response is None:  # pragma: no cover
        if alternatives:
            return None
        else:
            return None

    status = response["status"]

    if status in STATUS_CODES.keys():
        if status == "UNKNOWN_ERROR":
            error = RouterServerError

        elif status in ["OVER_QUERY_LIMIT", "OVER_DAILY_LIMIT"]:
            error = OverQueryLimit

        else:
            error = RouterApiError

        raise error(STATUS_CODES[status]["code"], STATUS_CODES[status]["message"])

    if alternatives:
        routes = []
        for route in response["routes"]:
            geometry = []
            (
                duration,
                duration_in_traffic,
                distance,
            ) = (
                0,
                0,
                0,
            )
            for leg in route["legs"]:
                duration_in_traffic += leg["duration_in_traffic"]["value"]
                duration += leg["duration"]["value"]
                distance += leg["distance"]["value"]
                for step in leg["steps"]:
                    geometry.extend(
                        routingpy.utils.decode_polyline5(step["polyline"]["points"])
                    )

            routes.append(
                GoogleRoute(
                    {
                        "geometry": geometry,
                        "duration": int(duration),
                        "duration_in_traffic": int(duration_in_traffic),
                        "distance": int(distance),
                        "raw": route,
                    }
                )
            )
        return routes
    else:
        geometry = []
        duration, duration_in_traffic, distance = 0, 0, 0
        for leg in response["routes"][0]["legs"]:
            duration_in_traffic = int(leg["duration_in_traffic"]["value"])
            duration = int(leg["duration"]["value"])
            distance = int(leg["distance"]["value"])
            for step in leg["steps"]:
                geometry.extend(
                    [
                        list(reversed(coords))
                        for coords in routingpy.utils.decode_polyline5(
                            step["polyline"]["points"]
                        )
                    ]
                )
        return GoogleRoute(
            {
                "geometry": geometry,
                "duration": duration,
                "duration_in_traffic": int(duration_in_traffic),
                "distance": distance,
                "raw": response,
            }
        )


def query_google_route(google_client, start_end_coordinates, departure_time):
    """
    Queries route from Google Directions API
    :param google_client:
    :param start_end_coordinates:
    :param departure_time:
    :return:
    """
    # route_google = google_client.directions(locations=start_end_coordinates,
    #                                        alternatives=True,
    #                                        profile="driving",
    #                                        departure_time=departure_time,
    #                                        traffic_model="best_guess")

    start = f"{start_end_coordinates[0][1]},{start_end_coordinates[0][0]}"
    end = f"{start_end_coordinates[1][1]},{start_end_coordinates[1][0]}"
    alternatives = True
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={start}&"
        f"destination={end}&"
        f"&key={os.getenv('GOOGLE_API_KEY')}&"
        f"departure_time={departure_time}&"
        f"alternatives=false&"
        f"traffic_model=best_guess"
    )
    payload = {}
    headers = {}

    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        route_google = _parse_direction_json(response.json(), alternatives)
    except Exception as e:
        print(e)
        return None

    if route_google is None:
        return None

    geometries = [LineString(r.coordinates) for r in route_google]
    durations_in_traffic = [r.duration_in_traffic for r in route_google]
    durations = [r.duration for r in route_google]
    distances = [r.distance for r in route_google]

    routes_google_df = gpd.GeoDataFrame(
        {
            "geometry": geometries,
            "duration_in_traffic": durations_in_traffic,
            "duration": durations,
            "distance": distances,
        },
        crs="epsg:4326",
    )
    routes_google_df.sort_values("duration", ascending=True, inplace=True)
    return routes_google_df


def generate_google_routes(aoi_file, n_routes, outfile):
    """
    Generates routes using Google Directions API
    :param aoi_file:
    :param api_key:
    :param n_routes:
    :param departure_time: Departure time in ISO format
    :param outfile:
    :return:
    """
    # departure times in epocs
    departure_times = pd.date_range("2023-06-14", periods=24, freq="H")

    aoi = gpd.read_file(aoi_file).geometry.cascaded_union
    google_client = routingpy.routers.Google(api_key=os.getenv("GOOGLE_API_KEY"))

    routes_collection = []
    with tqdm(total=n_routes * 24) as pbar:
        for departure_time in departure_times:
            i = 0
            while i < n_routes:
                start_end_coordinates = utils.get_random_coordinates(polygon=aoi)
                try:
                    routes = query_google_route(
                        google_client,
                        start_end_coordinates,
                        departure_time.strftime("%s"),
                    )
                except Exception as e:
                    print(e)
                    continue
                if routes is None:
                    continue
                routes["id"] = f"h{departure_time.strftime('%H')}_{i}"
                routes["departure_time"] = departure_time.isoformat()
                routes_collection.append(routes)
                i += 1
                pbar.update(1)

    routes_collection_df = gpd.GeoDataFrame(pd.concat(routes_collection, axis=0))
    routes_collection_df.to_file(outfile, driver="GeoJSON")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates routes using Google Directions API"
    )
    parser.add_argument(
        "--aoifile",
        "-a",
        required=True,
        dest="aoi_file",
        type=str,
        help="Path to the vector file containing polygon of AOI",
    )
    parser.add_argument(
        "--routes",
        "-r",
        required=False,
        default=50,
        dest="n_routes",
        type=str,
        help="Number of routes for each hour of the day",
    )
    parser.add_argument(
        "--outfile",
        "-o",
        required=True,
        dest="outfile",
        type=str,
        help="Path to output file",
    )
    args = parser.parse_args()

    generate_google_routes(
        aoi_file=args.aoi_file, n_routes=args.n_routes, outfile=args.outfile
    )
