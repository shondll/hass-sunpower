"""Constants for the Detailed Hello World Push integration."""

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "pvs6"

from .pypvs.pypvs.pvs import PVSAuthenticationError, PVSCommunicationError

from homeassistant.const import Platform

DOMAIN = "pvs6"

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]

INVALID_AUTH_ERRORS = (PVSAuthenticationError, PVSCommunicationError)

OPTION_UPDATE_PERIOD_S = "update_period_s"
OPTION_UPDATE_PERIOD_S_DEFAULT_VALUE = 5
OPTION_UPDATE_PERIOD_S_MIN_VALUE = 1
