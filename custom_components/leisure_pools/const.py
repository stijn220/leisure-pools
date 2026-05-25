DOMAIN = "leisure_pools"
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

BASE_URL = "http://{host}"
LOGIN_URL = f"{BASE_URL}/cgi/login"
WRITE_TAGS_URL = f"{BASE_URL}/cgi/writeTags.json"
SSE_PATH = "/cgi/sse"
PROJECT_PROPERTY = "projectRelativePath"
PROJECT_CONFIG_PATH = "web/web/config/conf.json"
FORCE_LOGIN_QUERY = "?forceLogin=true"

DEFAULT_MIN_PERIOD = 1000
GROUP_SUBSCRIPTION_CHUNK_SIZE = 4
EXTRA_SUBSCRIBED_TAGS = (
    "nPositieRolluik",
    "bCoverUnlocked",
    "nLichtKleur",
    "bColorChanging",
    "D160",
)

LIGHT_ENTITY_UNIQUE_ID = "pool_light"
COVER_ENTITY_UNIQUE_ID = "pool_cover"
LOCK_SWITCH_UNIQUE_ID = "pool_cover_lock"
LIGHT_COLOR_BUTTON_UNIQUE_ID = "pool_light_next_color"
PUMP_MODE_SELECT_UNIQUE_ID = "pool_pump_mode"

PUMP_MODE_AUTO = "auto"
PUMP_MODE_OFF = "uit"
PUMP_MODE_SPEED_1 = "speed 1"
PUMP_MODE_SPEED_2 = "speed 2"
PUMP_MODE_SPEED_3 = "speed 3"
PUMP_MODE_VACUUM = "vacuum"
PUMP_MODE_BACKWASH = "backwash"
PUMP_MODE_RINSE = "rinse"

PUMP_MODE_OPTIONS = (
    PUMP_MODE_AUTO,
    PUMP_MODE_OFF,
    PUMP_MODE_SPEED_1,
    PUMP_MODE_SPEED_2,
    PUMP_MODE_SPEED_3,
    PUMP_MODE_VACUUM,
    PUMP_MODE_BACKWASH,
    PUMP_MODE_RINSE,
)
