"""Basic Sunpower PVS Tool."""

import requests
import simplejson
from .pypvs.pypvs.pvs import PVS


class ConnectionException(Exception):
    """Any failure to connect to sunpower PVS."""


class ParseException(Exception):
    """Any failure to connect to sunpower PVS."""


class SunPowerMonitor:
    """Basic Class to talk to sunpower pvs 5/6 via the management interface 'API'.

    This is not a public API so it might fail at any time.
    if you find this useful please complain to sunpower and your sunpower dealer that they
    do not have a public API.
    """

    def __init__(self, host) -> None:
        """Initialize."""
        self.host = host
        self.command_url = f"http://{host}/cgi-bin/dl_cgi?Command="

        self.pvs = PVS(port=20566)
        self.pvs.ip = self.host
        self.pvs.update_clients()

        # Use JWT authentication
        # comment out to use basic authentication
        self.pvs.fcgi_client.set_jwt_request_url("https://pvs-auth-mgr.dev.mysunpower.com:443/v1/auth/token")
        self.pvs.fcgi_client.set_pvs_details(
            {
                "serial": "ZT190885000549A1562",
                "ssid": "SunPower08562",
                "wpa_key": "CD4A828E",
                "mac": "00:22:F2:0B:48:60",
                "client_id": "ALsuV7T7IVqJn9yISPqii4oZi4gq6bWaQYH6mff1wPXYtUzgzc",
            }
        )

    def generic_command(self, command):
        """All 'commands' to the PVS module use this url pattern and return json.

        The PVS system can take a very long time to respond so timeout is at 2 minutes.
        """
        try:
            return requests.get(self.command_url + command, timeout=120).json()
        except requests.exceptions.RequestException as error:
            raise ConnectionException from error
        except simplejson.errors.JSONDecodeError as error:
            raise ParseException from error

    def device_list(self):
        """Get a list of all devices connected to the PVS."""

        resp = self.generic_command("DeviceList")
        uptime = self.pvs.getVarserverVar("/sys/info/uptime")
        resp["varserver_uptime"] = uptime

        print(resp)
        return resp

    def energy_storage_system_status(self):
        """Get the status of the energy storage system."""
        try:
            return requests.get(
                f"http://{self.host}/cgi-bin/dl_cgi/energy-storage-system/status",
                timeout=120,
            ).json()
        except requests.exceptions.RequestException as error:
            raise ConnectionException from error
        except simplejson.errors.JSONDecodeError as error:
            raise ParseException from error

    def network_status(self):
        """Get a list of network interfaces on the PVS."""
        return self.generic_command("Get_Comm")
