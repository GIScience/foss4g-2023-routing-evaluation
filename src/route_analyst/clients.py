#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ORS routing client"""

import openrouteservice as ors

from .responses import ORSDirectionsResponse


class ORSRoutingClient:
    """Create ORS routing client to send requests to ORS server"""

    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initializes parameters and sends request to ORS server
        :param base_url: server address of ORS routing server
        :param api_key: ORS API key
        """
        self.base_url = base_url  # if base_url else
        self.api_key = api_key
        self.__headers = {
            "headers": {
                "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
                "Authorization": f"{api_key}",
                "Content-Type": "application/json; charset=utf-8",
            }
        }
        if self.base_url:
            self.client = ors.Client(base_url=self.base_url)
        else:
            self.client = ors.Client(key=self.api_key)

    def request(self, params: dict, profile: str, format: str):
        """
        Send route request to ORS server

        :param params: dict containing request parameters
        :param profile: Name of routing profile
        :param format: Output format
        :return: dict of ORS response
        """
        try:
            response = self.client.request(
                url=f"/v2/directions/{profile}/{format}",
                post_json=params,
                requests_kwargs=self.__headers,
                get_params=[],
            )
            return ORSDirectionsResponse(response)
        except ors.exceptions.ApiError as e:
            raise ValueError(e.message)
