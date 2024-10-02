"""Basic Sunpower PVS Tool."""

import requests
import simplejson
import logging
from .pypvs.pypvs.pvs import PVS

from .const import LIVEDATA_DEVICE_TYPE, PVS_DEVICE_TYPE

_LOGGER = logging.getLogger(__name__)

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

    def __init__(self, host, session) -> None:
        """Initialize."""
        self.host = host
        self.command_url = f"http://{host}/cgi-bin/dl_cgi?Command="

        client_id = "ALsuV7T7IVqJn9yISPqii4oZi4gq6bWaQYH6mff1wPXYtUzgzc"
        self.pvs = PVS(port=20566, session=session, client_id=client_id)
        self.pvs.ip = self.host
        self.pvs.sn = "ZT190885000549A1562"
        self.pvs.update_clients()

        # Use JWT authentication
        # comment out to use basic authentication
        self.pvs.fcgi_client.set_jwt_request_url(
            "https://pvs-auth-mgr.dev.mysunpower.com:443/v1/auth/token"
        )
        self.pvs.fcgi_client.set_pvs_details(
            {
                "serial": self.pvs.sn,
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
        # uptime = self.pvs.getVarserverVar("/sys/info/uptime")
        # resp["varserver_uptime"] = uptime

        # print(resp)
        return resp

    async def get_pvs_info(self):
        """Get a list of all devices connected to the PVS."""
        pvs_info = {}
        try:
            pvs_info = await self.pvs.getVarserverVars("/sys/info")
            pvs_info["/sys/info/uptime"] = await self.pvs.getVarserverVar("/sys/info/uptime")
            pvs_info["/sys/info/mem_used"] = 9999
            pvs_info["/sys/info/flash_avail"] = 88888
            pvs_info["STATE"] = "ONLINE"
        except Exception as error:
            _LOGGER.exception(f"Failed to get PVS info!")
            pvs_info["STATE"] = "OFFLINE"

        pvs_info["DEVICE_TYPE"] = PVS_DEVICE_TYPE
        pvs_info["SERIAL"] = self.pvs.sn
        pvs_info["DESCR"] = "PV Supervisor"

        return pvs_info

    async def get_livedata(self):
        """Get the current live data from the PVS."""
        livedata = {}
        try:
            livedata = await self.pvs.getVarserverVars("/sys/livedata")
            livedata["STATE"] = "ONLINE"
        except Exception as error:
            _LOGGER.exception(f"Failed to get live data!")
            livedata["STATE"] = "OFFLINE"

        livedata["DEVICE_TYPE"] = LIVEDATA_DEVICE_TYPE
        livedata["SERIAL"] = self.pvs.sn
        livedata["DESCR"] = "Live Data"

        return livedata

    async def get_sn(self):
        # return self.pvs.get_sn()
        sn = await self.pvs.getVarserverVar("/sys/info/sn")
        return sn

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
