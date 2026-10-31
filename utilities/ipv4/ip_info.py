import socket
from dataclasses import dataclass
from typing import Optional, List
import requests

@dataclass
class IPInfoFormat:
    continent: Optional[str] = None
    continent_code: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    region_name: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    isp: Optional[str] = None
    org: Optional[str] = None
    domains: List[str] = None

class IPInfo:
    def __init__(self, ip_address: str, reverse: bool = False):
        '''
        Initialize the class with the provided IP address and optional reverse flag.

        :param ip_address: The IP address to be associated with the instance.
        :param reverse: A flag indicating whether the operation should be reversed. Defaults to False.
        '''
        self.ip_address = ip_address
        self.reverse = reverse
        self.domains = []

    def get_info(self) -> Optional[IPInfoFormat]:
        '''
        Get the information of the IP address
        :return: The information of the IP address or None if the request fails
        '''
        try:
            url = f"http://ip-api.com/json/{self.ip_address}?fields=status,message,continent,continentCode,country,countryCode,region,regionName,city,timezone,isp,org,as,asname,reverse,query"
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") != "success":
                return None
            return IPInfoFormat(
                continent=data.get("continent"),
                continent_code=data.get("continentCode"),
                country=data.get("country"),
                country_code=data.get("countryCode"),
                region=data.get("region"),
                region_name=data.get("regionName"),
                city=data.get("city"),
                timezone=data.get("timezone"),
                isp=data.get("isp"),
                org=data.get("org"),
                domains=self.domains
            )
        except requests.RequestException:
            return None