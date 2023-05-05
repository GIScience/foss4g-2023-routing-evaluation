#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes to handle responses and read route information"""

import json
from pathlib import Path

from .routes import ORSRoute, GoogleRoute


class ORSDirectionsResponse:
    """Response from ORS server"""

    def __init__(self, json_response: dict = None, file: Path = None):
        """Reads and handles response"""
        if json_response:
            self.json_response = json_response
        elif file:
            self.json_response = self.load(file)
        self.routes = []
        self._extract_routes()

    def _extract_routes(self):
        """
        Get routes and their alternatives
        :return: List containing maximum 3 Route objects (1 route and 2 or less alternative routes)
        """
        for route_feature in self.json_response["features"]:
            self.routes.append(ORSRoute(json_response=route_feature))

    def _extract_metadata(self):
        """
        Parses metadata from raw json response
        :return:
        """
        pass

    def from_file(self, file):
        """
        Loads route from file
        :param file:
        :return:
        """
        with open(file) as src:
            self.json_response = json.load(src)

    def to_file(self, file):
        """
        Writes route to json file
        :param file:
        :return:
        """
        with open(file, "w") as dst:
            json.dump(self.json_response, dst)


class GoogleDirectionsResponse:
    """Response from Google Directions API"""

    def __init__(self, json_response: dict = None, file: Path = None):
        """Reads and handles response"""
        if json_response:
            self.json_response = json_response
        elif file:
            self.json_response = self.load(file)
        self.routes = self._parse_direction_json()
        self._extract_routes()

    def _extract_routes(self):
        """
        Get routes and their alternatives
        :return: List containing maximum 3 Route objects (1 route and 2 or less alternative routes)
        """
        for route_feature in self.json_response["routes"]:
            self.routes.append(GoogleRoute(json_response=route_feature))

    def _extract_metadata(self):
        """
        Parses metadata from raw json response
        :return:
        """
        pass

    def from_file(self, file):
        """
        Loads route from file
        :param file:
        :return:
        """
        with open(file) as src:
            self.json_response = json.load(src)
