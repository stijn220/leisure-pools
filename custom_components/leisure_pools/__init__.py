DOMAIN = 'leisure_pools'

async def async_setup(hass, config):
    hass.states.async_set("leisure_pools.world", "Paulus")

    # Return boolean to indicate that initialization was successful.
    return True