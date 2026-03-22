DOMAIN = "leisure_pool"
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
)

LIGHT_ENTITY_UNIQUE_ID = "pool_light"
COVER_ENTITY_UNIQUE_ID = "pool_cover"
LOCK_SWITCH_UNIQUE_ID = "pool_cover_lock"
