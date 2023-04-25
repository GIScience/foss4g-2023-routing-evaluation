import openrouteservice as ors
import requests

from route_analyst import ORSDirectionsResponse


class ORSRoutingClient:
    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initializes parameters and sends request to ORS server
        :param params: dict
        :param base_url: string
        """
        self.base_url = base_url  # if base_url else
        self.api_key = api_key
        self.__headers = {
            "headers": {
                "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
                "Authorization": "{}".format(api_key),
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

        :param profile: Name of routing profile
        :param format: Output format
        :param params: dict containing request parameters
        :return: dict of ORS response
        """
        try:
            response = self.client.request(
                url="/v2/directions/{}/{}".format(profile, format),
                post_json=params,
                requests_kwargs=self.__headers,
                get_params=[],
            )
            return ORSDirectionsResponse(response)
        except ors.exceptions.ApiError as e:
            raise ValueError(e.message)


class GoogleRoutingClient:
    def __init__(self, api_key: str = None):
        """
        Initializes parameters and sends request to ORS server
        :param params: dict
        :param base_url: string
        """
        self.api_key = api_key
        self.__headers = headers = {
            "headers": {
                "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
                "Content-Type": "application/json; charset=utf-8",
            }
        }

    def request(self, params: dict):
        """
        Send route request to ORS server

        :param profile: Name of routing profile
        :param format: Output format
        :param params: dict containing request parameters
        :return: dict of ORS response
        """
        try:
            url = (
                f"https://maps.googleapis.com/maps/api/directions/json?"
                f"origin={params['start']}&"
                f"destination={params['end']}&"
                f"&key={self.api_key}&"
                f"departure_time={params['departure_time']}&"
                f"alternatives=false&"
                f"traffic_model=best_guess"
            )
            payload = {}
            headers = {}

            return requests.request("GET", url, headers=headers, data=payload)
        except Exception as e:
            print.info(e)
            return None

    def parse_respons(self):
        pass
        # route_google = _parse_direction_json(response.json, alternatives)
