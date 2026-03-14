"""Constants for the RTE Tempo Calendar integration."""
from zoneinfo import ZoneInfo

DOMAIN = "rtetempo"


# Config Flow

CONFIG_CLIENT_ID = "client_id"
CONFIG_CLIEND_SECRET = "client_secret"
OPTION_ADJUSTED_DAYS = "adjusted_days"
OPTION_FORECAST_ENABLED = "forecast_enabled"


# Service Device

DEVICE_NAME = "RTE Tempo"
DEVICE_MANUFACTURER = "RTE"
DEVICE_MODEL = "Calendrier Tempo"


# Sensors

SENSOR_COLOR_BLUE_NAME = "Bleu"
SENSOR_COLOR_BLUE_EMOJI = "🔵"
SENSOR_COLOR_WHITE_NAME = "Blanc"
SENSOR_COLOR_WHITE_EMOJI = "⚪"
SENSOR_COLOR_RED_NAME = "Ro" + "uge"  # codespell workaround
SENSOR_COLOR_RED_EMOJI = "🔴"
SENSOR_COLOR_UNKNOWN_NAME = "inconnu"
SENSOR_COLOR_UNKNOWN_EMOJI = "❓"


# API

FRANCE_TZ = ZoneInfo("Europe/Paris")
API_DOMAIN = "digital.iservices.rte-france.com"
API_TOKEN_ENDPOINT = f"https://{API_DOMAIN}/token/oauth"
API_TEMPO_ENDPOINT = (
    f"https://{API_DOMAIN}/open_api/tempo_like_supply_contract/v1/tempo_like_calendars"
)
API_REQ_TIMEOUT = 3
API_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
API_KEY_ERROR = "error"
API_KEY_ERROR_DESC = "error_description"
API_KEY_RESULTS = "tempo_like_calendars"
API_KEY_VALUES = "values"
API_KEY_START = "start_date"
API_KEY_END = "end_date"
API_KEY_VALUE = "value"
API_KEY_UPDATED = "updated_date"
API_VALUE_RED = "RED"
API_VALUE_WHITE = "WHITE"
API_VALUE_BLUE = "BLUE"
API_ATTRIBUTION = "Données fournies par data.rte-france.com"
USER_AGENT = "github.com/hekmon/rtetempo v1.6.3"


# Tempo def

HOUR_OF_CHANGE = 6
OFF_PEAK_START = 22
TOTAL_RED_DAYS = 22
TOTAL_WHITE_DAYS = 43
CYCLE_START_MONTH = 9
CYCLE_START_DAY = 1
CONFIRM_HOUR = 10
CONFIRM_MIN = 40
CONFIRM_CHECK = 11


# Resilience / source strategy

OPTION_SOURCE_MODE = "source_mode"
OPTION_FALLBACK_STRATEGY = "fallback_strategy"
OPTION_DEFAULT_TODAY_COLOR = "default_today_color"
OPTION_DEFAULT_TOMORROW_COLOR = "default_tomorrow_color"

OPTION_LOCAL_TODAY_ENTITY = "local_today_entity"
OPTION_LOCAL_TOMORROW_ENTITY = "local_tomorrow_entity"
OPTION_LOCAL_HCHP_ENTITY = "local_hchp_entity"

SOURCE_MODE_WEB = "web"
SOURCE_MODE_LOCAL = "local"
SOURCE_MODE_AUTO = "auto"
SOURCE_MODE_COMPARE = "compare"
SOURCE_MODE_DEFAULT = "default"

FALLBACK_LAST_GOOD = "last_good"
FALLBACK_DEFAULT = "default"
FALLBACK_UNKNOWN = "unknown"

RESOLVER_SOURCE_RTE = "web"
RESOLVER_SOURCE_LOCAL = "local"
RESOLVER_SOURCE_DEFAULT = "default"
RESOLVER_SOURCE_FORECAST = "forecast"

SOURCE_STATUS_NOMINAL = "nominal"
SOURCE_STATUS_DEGRADED = "dégradé"
SOURCE_STATUS_FALLBACK = "fallback"
SOURCE_STATUS_UNAVAILABLE = "indisponible"

COLOR_BLUE = "blue"
COLOR_WHITE = "white"
COLOR_RED = "red"
COLOR_UNKNOWN = "unknown"

SOURCE_MODE_OPTIONS = [
    SOURCE_MODE_AUTO,
    SOURCE_MODE_WEB,
    SOURCE_MODE_LOCAL,
    SOURCE_MODE_DEFAULT,
    SOURCE_MODE_COMPARE,
]

RUNTIME_SOURCE_MODE_OPTIONS = [
    SOURCE_MODE_AUTO,
    SOURCE_MODE_WEB,
    SOURCE_MODE_LOCAL,
    SOURCE_MODE_DEFAULT,
]

FALLBACK_STRATEGY_OPTIONS = [
    FALLBACK_UNKNOWN,
    FALLBACK_DEFAULT,
    FALLBACK_LAST_GOOD,
]

DEFAULT_COLOR_OPTIONS = [
    COLOR_UNKNOWN,
    COLOR_BLUE,
    COLOR_WHITE,
    COLOR_RED,
]
