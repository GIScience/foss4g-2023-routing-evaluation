#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Route classes"""

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt


class ORSRoute(object):
    """Route calculated using openrouteservice"""

    __dataframe = None

    def __init__(self, json_response):
        """Initializes parameters and sends request to ORS server"""
        self.__json_response = json_response

    @property
    def json_response(self):
        """Returns the ORS response as a dictionary"""
        return self.__json_response

    @property
    def coordinates(self):
        """
        Returns the coordinates of the route from the ORS response
        :return: list of coordinates
        """
        return self.json_response["geometry"]["coordinates"]

    @property
    def geometry(self):
        """
        Returns the geometry of the route
        :return: LineString object
        """
        return LineString(self.coordinates)

    @property
    def summary(self):
        """
        Returns the summary of the route
        :return:
        """
        return self.json_response["properties"]["summary"]

    @property
    def extras(self):
        """
        Returns the extra information from the ORS response
        :return:
        """
        try:
            return self.json_response["properties"]["extras"]
        except Exception:
            return None

    def values(self, criteria):
        """
        Returns the values for a certain criterion
        :param criterion: 'green', 'noise' or 'steepness'
        :return: values of criterion along route
        """
        return np.concatenate(
            [np.repeat(v[2], v[1] - v[0]) for v in self.extras[criteria]["values"]]
        )

    @property
    def steepness_exposure(self):
        """
        Returns the overall exposure to positive and negative steepness of the route
        :return: steepness exposure for negative and positive values
        """
        summary = self.summary_criterion("steepness")
        pos = []
        neg = []
        dist_Neg = []
        dist_Pos = []
        for o in range(len(summary["value"])):
            if summary["value"][o] > 0:
                pos.append(summary["value"][o])
                dist_Pos.append(summary["distance"][o])
            else:
                neg.append(summary["value"][o])
                dist_Neg.append(summary["distance"][o])

        if sum(dist_Neg) != 0:
            res2 = sum(np.array(neg) * np.array(dist_Neg)) / sum(dist_Neg)
        else:
            res2 = np.nan
        if sum(dist_Pos) != 0:
            res1 = sum(np.array(pos) * np.array(dist_Pos)) / sum(dist_Pos)
        else:
            res1 = np.nan
        return [res1, res2]

    @property
    def noise_exposure(self):
        """Returns the overall exposure to noise of the route"""
        summary = self.summary_criterion("noise")
        return sum(summary["value"] * summary["distance"]) / summary["distance"].sum()

    @property
    def duration(self):
        """Returns the overall duration of the route"""
        return self.summary["duration"]

    @property
    def distance(self):
        """Returns the overall distance of the route"""
        return self.summary["distance"]

    @property
    def descent(self):
        """Returns the overall distance of the route"""
        return self.json_response["properties"]["descent"]

    @property
    def ascent(self):
        """
        Returns the overall distance of the route
        :return: ascent value
        """
        return self.json_response["properties"]["ascent"]

    def summary_criterion(self, criterion):
        """
        Returns the summary for a certain criterion of the ORS response as a pandas dataframe
        :param criterion: 'green', 'noise' or 'steepness'
        :return: Dataframe with summary
        """
        if criterion in self.extras.keys():
            return pd.DataFrame(self.extras[criterion]["summary"])
        else:
            raise ValueError("criterion '%s' does not exist.")

    def plot_summary(self, criterion):
        """
        Returns a bar plot of the summary for a certain criterion
        :param criterion: 'green', 'noise' or 'steepness'
        :return: Bar plot showing summary
        """
        summary = self.summary_criterion(criterion)
        return plt.bar(x=summary["value"], height=summary["amount"], color="green")

    @property
    def route_segments(self):
        """
        Returns segments of the route
        :return: list of LineStrings
        """
        n_segments = len(self.coordinates) - 1
        segments = []
        for i in range(0, n_segments):
            segments.append(LineString(self.coordinates[i : i + 2]))
        return segments

    # todo write test for this function
    def as_dataframe(self):
        """
        Converts the route and its extra information into a geopandas dataframe
        :return: GeoDataFrame with route information
        """
        if self.__dataframe is not None:
            return self.__dataframe
        else:
            df = gpd.GeoDataFrame({"geometry": self.route_segments}, crs="epsg:4326")
            if self.extras:
                for k in self.extras.keys():
                    df[k] = self.values(k)
                # Dissolve line strings
                columns = list(df.columns.drop("geometry"))
                df = df.dissolve(by=columns, as_index=True).reset_index()
                df = df.loc[~df.is_empty]
                df.geometry = df.geometry.apply(
                    lambda x: MultiLineString([x]) if isinstance(x, LineString) else x
                )
        self.__dataframe = df
        return self.__dataframe

    def to_geojson(self, outfile, driver):
        """
        Writes the route to a geojson file
        :param outfile: Path to output file as string
        :return: geojson file
        """
        self.as_dataframe().to_file(outfile, driver=driver)

    def plot(self, *args, **kwargs):
        """
        Plots the route on a map
        :param args:
        :param kwargs:
        :return: plotted route
        """
        return self.as_dataframe().plot(*args, **kwargs)

    def to_file(self, outfile):
        """
        Writes the whole response to file
        :param outfile: Object of type Route
        :return: json file
        """
        with open(outfile, "w") as dst:
            json.dump(self.json_response, dst, indent=4)

    def duration_diff_sec(self, other_route):
        """
        Calculates the duration difference in minutes between this route and another route object
        :param other route: Object of type Route
        :return: duration difference value in seconds
        """
        return self.duration - other_route.duration_in_traffic

    def duration_diff_perc(self, other_route):
        """
        Calculates the duration difference in percent between this route and another route object
        :param other route: Object of type Route
        :return: duration deviation value (difference in percent)
        """
        return (self.duration - other_route.duration_in_traffic) / self.duration * 100

    def distance_diff_meter(self, other_route):
        """
        Calculates the duration difference in meters between this route and another route object
        :param other route: Object of type Route
        :return: distance difference value in meters
        """
        return self.distance - other_route.distance

    def distance_diff_perc(self, other_route):
        """
        Calculates the duration difference in percent between this route and another route object
        :param other route: Object of type Route
        :return: distance deviation value (difference in percent)
        """
        return (self.distance - other_route.distance) / self.distance * 100

    def geometry_diff_perc(self, other_route):
        """
        Calculates the geometry deviation in percent of this route and another route object
        :param other route: Object of type Route
        :return: geometry deviation (difference in percent)
        """
        same = self.geometry.intersection(other_route.geometry.buffer(0.0001))
        return (self.geometry.length - same.length) / self.geometry.length * 100

    def geometry_diff_hausdorff(self, other_route):
        """
        Calculates the hausdorff distance between this route and another route object and returns the value
        :param other route: Object of type Route
        :return: hausdorff distance value
        """
        return self.geometry.hausdorff_distance(other_route.geometry)


class GoogleRoute(object):
    """Route calculated using Google Directions API"""

    __dataframe = None
    extras = False

    def __init__(self, json_response):
        """
        Initializes parameters and sends request to ORS server

        :param params: dict
        :param base_url: string
        """
        self.__json_response = json_response

    @property
    def json_response(self):
        """Returns the ORS response as a dictionary"""
        return self.__json_response

    @property
    def id(self):
        """Returns the id of the route"""
        return self.json_response["id"]

    @property
    def coordinates(self):
        """
        Returns the coordinates of the route from the ORS response
        :return: list of coordinates
        """
        return self.json_response["geometry"]

    @property
    def geometry(self):
        """Returns the geometry of the route"""
        return LineString(self.coordinates)

    @property
    def duration(self):
        """Returns the overall duration of the route"""
        return self.json_response["duration"]

    @property
    def duration_in_traffic(self):
        """Returns the overall duration of the route with traffic"""
        return self.json_response["duration_in_traffic"]

    @property
    def distance(self):
        """Returns the overall distance of the route"""
        return self.json_response["distance"]

    @property
    def departure(self):
        """Returns the departure time of the route"""
        return self.json_response["departure_time"]

    @property
    def hour(self):
        """Returns the hour of the departure time"""
        return self.json_response["hour"]

    @property
    def route_segments(self):
        """
        Returns segments of the route
        :return: list of LineStrings
        """
        n_segments = len(self.coordinates) - 1
        segments = []
        for i in range(0, n_segments):
            segments.append(LineString(self.coordinates[i : i + 2]))
        return segments

    # todo write test for this function
    def as_dataframe(self):
        """
        Converts the route and its extra information into a geopandas dataframe
        :return: GeoDataFrame with route information
        """
        if self.__dataframe is not None:
            return self.__dataframe
        else:
            df = gpd.GeoDataFrame({"geometry": self.route_segments}, crs="epsg:4326")
            if self.extras:
                for k in self.extras.keys():
                    df[k] = self.values(k)
                # Dissolve line strings
                columns = list(df.columns.drop("geometry"))
                df = df.dissolve(by=columns, as_index=True).reset_index()
                df = df.loc[~df.is_empty]
                df.geometry = df.geometry.apply(
                    lambda x: MultiLineString([x]) if isinstance(x, LineString) else x
                )
        self.__dataframe = df
        return self.__dataframe

    def to_geojson(self, outfile, driver):
        """
        Writes the route to a geojson file
        :param outfile: Path to output file as string
        :return:
        """
        self.as_dataframe().to_file(outfile, driver=driver)

    def plot(self, *args, **kwargs):
        """
        Plots the route on a map
        :param args:
        :param kwargs:
        :return: plotted route
        """
        return self.as_dataframe().plot(*args, **kwargs)

    def to_file(self, outfile):
        """
        Writes the whole response to file
        :param outfile: path to outfile
        :return: json file
        """
        with open(outfile, "w") as dst:
            json.dump(self.json_response, dst, indent=4)
