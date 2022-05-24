from typing import List
from pydantic import BaseModel


class GeocodeResult(BaseModel):
    """
    A basic abstract class representing a successful geocoding response.
    SmartyStreets asks us to implement a custom result to wrap their
    base model in for ease of working with.
    """

    address: List[str]
    city: str
    state: str
    zipcode: str
    county_fips: str
    county_name: str
    lat: float
    lng: float
    precision: str
