"""Basic Sunpower PVS Tool."""

import requests
import simplejson
import logging
from .pypvs.pypvs.pvs import PVS

from .const import LIVEDATA_DEVICE_TYPE, PVS_DEVICE_TYPE, INVERTER_DEVICE_TYPE, METER_DEVICE_TYPE

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
            pvs_info_tmp = await self.pvs.getVarserverVars("/sys/info")
            # pvs_info_tmp["/sys/info/uptime"] = await self.pvs.getVarserverVar(
            #     "/sys/info/uptime"
            # )
            pvs_info_tmp["/sys/info/mem_used"] = 9999
            pvs_info_tmp["/sys/info/flash_avail"] = 88888
            pvs_info_tmp["STATE"] = "ONLINE"

            pvs_info_tmp["HWVER"] = pvs_info_tmp.get("/sys/info/hwrev", "Unknown")
            pvs_info_tmp["SWVER"] = pvs_info_tmp.get("/sys/info/sw_rev", "Unknown")

            pvs_info = pvs_info_tmp
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
            livedata_tmp = await self.pvs.getVarserverVars("/sys/livedata")
            livedata_tmp["STATE"] = "ONLINE"
            livedata = livedata_tmp
        except Exception as error:
            _LOGGER.exception(f"Failed to get live data!")
            livedata["STATE"] = "OFFLINE"

        livedata["DEVICE_TYPE"] = LIVEDATA_DEVICE_TYPE
        livedata["SERIAL"] = self.pvs.sn
        livedata["DESCR"] = "Live Data"

        return livedata

    async def get_inverter_data(self):
        """Get the current inverter values from the PVS."""
        inverter_data = []
        try:
            inverter_data_tmp = await self.pvs.getVarserverVars("/inverter/data")
            # inverter_data_tmp = {
            #     "/sys/devices/14/inverter/data": {
            #         "inverterParameters": [
            #             {
            #                 "freqHz": 59.99,
            #                 "i3phsumA": 1.6,
            #                 "iMppt1A": 8.2,
            #                 "ltea3phsumKwh": 1913.7775241721856,
            #                 "msmtEps": "2024-09-30T16:15:00Z",
            #                 "p3phsumKw": 0.38278,
            #                 "pMppt1Kw": 0.3954,
            #                 "prodMdlNm": "AC_Module_Type_H",
            #                 "sn": "E00122244069288",
            #                 "tHtsnkDegc": 44,
            #                 "vMppt1V": 48.195,
            #                 "vldFld2Msk": "1",
            #                 "vldFldMsk": "8125",
            #                 "vln3phavgV": 238.06,
            #             }
            #         ]
            #     },
            #     "/sys/devices/15/inverter/data": {
            #         "inverterParameters": [
            #             {
            #                 "freqHz": 59.995,
            #                 "i3phsumA": 1.605,
            #                 "iMppt1A": 8.495,
            #                 "ltea3phsumKwh": 1913.358917880795,
            #                 "msmtEps": "2024-09-30T16:15:00Z",
            #                 "p3phsumKw": 0.38276,
            #                 "pMppt1Kw": 0.40422,
            #                 "prodMdlNm": "AC_Module_Type_H",
            #                 "sn": "E00122244069448",
            #                 "tHtsnkDegc": 44,
            #                 "vMppt1V": 47.57,
            #                 "vldFld2Msk": "1",
            #                 "vldFldMsk": "8125",
            #                 "vln3phavgV": 238.03,
            #             }
            #         ]
            #     },
            # }

            # iterate over the values only
            for item in inverter_data_tmp.values():
                inverter = item["inverterParameters"][0]
                inverter["STATE"] = "ONLINE"
                inverter["DEVICE_TYPE"] = INVERTER_DEVICE_TYPE
                inverter["DESCR"] = inverter["prodMdlNm"]
                inverter["SERIAL"] = inverter["sn"]
                inverter_data.append(inverter)
        except Exception as error:
            _LOGGER.exception(f"Failed to get inverter data!")

        return inverter_data

    async def get_meter_data(self):
        """Get the current meter values from the PVS."""
        meter_data = []
        try:
            # meter_data_tmp = await self.pvs.getVarserverVars("/meter/data")
            meter_data_tmp = {
                '/sys/devices/7/meter/data':
                    {
                        "meterParameters": [
                            {
                                "ctSclFctr": 50,
                                "freqHz": 59.9996452,
                                "msmtEps": "2024-09-30T16:15:00Z",
                                "netLtea3phsumKwh": 250.35,
                                "p3phsumKw": 1.92376637,
                                "prodMdlNm": "PVS6M0400p",
                                "q3phsumKvar": -0.0224891528,
                                "s3phsumKva": 1.9249469,
                                "sn": "PVS6M21360528p",
                                "totPfRto": 0.999190927,
                                "v12V": 237.034164,
                                "vldFldMsk": "67174655"
                            }
                        ]
                    },
                '/sys/devices/8/meter/data':
                    {
                        "meterParameters": [
                            {
                                "ctSclFctr": 100,
                                "freqHz": 59.9996452,
                                "i1A": 7.64965868,
                                "i2A": 7.7078824,
                                "msmtEps": "2024-09-30T16:15:00Z",
                                "negLtea3phsumKwh": 247.82999999999998,
                                "netLtea3phsumKwh": -230.81,
                                "p1Kw": -0.869951546,
                                "p2Kw": -0.87526238,
                                "p3phsumKw": -1.74521399,
                                "posLtea3phsumKwh": 17.03,
                                "prodMdlNm": "PVS6M0400c",
                                "q3phsumKvar": -0.483921409,
                                "s3phsumKva": 1.82013345,
                                "sn": "PVS6M21360528c",
                                "totPfRto": -0.960669816,
                                "v12V": 237.034164,
                                "v1nV": 118.475601,
                                "v2nV": 118.558769,
                                "vldFldMsk": "70239999"
                            }
                        ]
                    }
            }

            # iterate over the values only
            for item in meter_data_tmp.values():
                meter = item["meterParameters"][0]
                meter["STATE"] = "ONLINE"
                meter["DEVICE_TYPE"] = METER_DEVICE_TYPE
                meter["DESCR"] = meter["prodMdlNm"]
                meter["SERIAL"] = meter["sn"]

                meter_data.append(meter)
        except Exception as error:
            _LOGGER.exception(f"Failed to get meter data!")

        return meter_data

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
