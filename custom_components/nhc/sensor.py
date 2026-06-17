import os
import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.template import Template
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up NHC sensors from a UI config entry handler."""
    # This acts as a bridge, routing the UI startup straight into your existing setup code
    await async_setup_platform(hass, {}, async_add_entities)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities,
    discovery_info: DiscoveryInfoType = None
) -> None:
    """Set up the self-contained NHC data fetcher and child templates."""
    _LOGGER.info("Starting up modern NHC platform sensor rendering sequence...")

    # Resolve path to nhc.jinja and load it safely
    current_dir = os.path.dirname(__file__)
    template_path = os.path.join(current_dir, "nhc.jinja")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            shared_macros = f.read()
    except Exception as err:
        _LOGGER.error("Failed to load nhc.jinja file contents: %s", err)
        return

    # Initialize the Primary Data Fetching REST Sensor
    master_fetcher_sensor = NHCMasterFetcherSensor(
        name="NHC Storm Data",
        unique_id="nhc_storm_data"
    )

    # Dynamic Loop to Build the Child Storm Entities
    storm_entities = []
    regions = {
        "Atlantic": "AT",
        "Eastern Pacific": "EP"
    }

    for region_name, prefix in regions.items():
        for i in range(1, 6):
            storm_code = f"{prefix}{i}"
            unique_id_str = f"nhc_storm_{prefix.lower()}{i}"
            display_name = f"{region_name} Storm {i}"

            state_tmpl = Template(shared_macros + f"{{{{ get_state('{storm_code}') }}}}", hass)
            
            attr_templates = {
                "friendly_name": Template(shared_macros + f"{{{{ get_classification('{storm_code}') }}}} {{{{ get_name('{storm_code}') }}}}", hass),
                "storm_name": Template(shared_macros + f"{{{{ get_name('{storm_code}') }}}}", hass),
                "classification": Template(shared_macros + f"{{{{ get_classification('{storm_code}') }}}}", hass),
                "pressure": Template(shared_macros + f"{{{{ get_pressure('{storm_code}') }}}}", hass),
                "intensity": Template(shared_macros + f"{{{{ get_intensity('{storm_code}') }}}}", hass),
                "max_winds": Template(shared_macros + f"{{{{ get_max_winds('{storm_code}') }}}}", hass),
                "heading": Template(shared_macros + f"{{{{ get_heading('{storm_code}') }}}}", hass),
                "heading_text": Template(shared_macros + f"{{{{ get_heading_text('{storm_code}') }}}}", hass),
                "movement_speed": Template(shared_macros + f"{{{{ get_movement_speed('{storm_code}') }}}}", hass),
                "distance": Template(shared_macros + f"{{{{ get_distance('{storm_code}') }}}}", hass),
                "latitude": Template(shared_macros + f"{{{{ get_latitude('{storm_code}') }}}}", hass),
                "longitude": Template(shared_macros + f"{{{{ get_longitude('{storm_code}') }}}}", hass),
                "region": Template(shared_macros + f"{{{{ get_region('{storm_code}') }}}}", hass),
                "forecast_discussion": Template(shared_macros + f"{{{{ get_forecast_discussion('{storm_code}') }}}}", hass),
                "forecast_graphics": Template(shared_macros + f"{{{{ get_forecast_graphics('{storm_code}') }}}}", hass),
            }

            storm_entities.append(
                NHCChildTemplateSensor(
                    name=display_name,
                    unique_id=unique_id_str,
                    state_template=state_tmpl,
                    attribute_templates=attr_templates
                )
            )

    # Register the master parent fetcher first, then the dependent loops
    async_add_entities([master_fetcher_sensor], update_before_add=True)
    async_add_entities(storm_entities, update_before_add=False)

    _LOGGER.info("Successfully registered self-contained NHC tracking stack.")


class NHCMasterFetcherSensor(SensorEntity):
    """The parent REST sensor that calls NOAA, stores activeStorms in attributes, and tracks count."""

    def __init__(self, name, unique_id):
        """Initialize the data gatherer."""
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = "mdi:database-import"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {"activeStorms": []}

    async def async_update(self) -> None:
        """Fetch the JSON payload from the NHC API safely without thread blocking."""
        url = "https://www.nhc.noaa.gov/CurrentStorms.json"
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    storms_list = data.get("activeStorms", [])
                    
                    # Update the state to show the total number of storms
                    self._attr_native_value = len(storms_list)
                    
                    # Dump the complete raw node right into this REST sensor's attributes array
                    self._attr_extra_state_attributes = {"activeStorms": storms_list}
                else:
                    _LOGGER.error("NHC API responded with server status code: %s", response.status)
        except Exception as err:
            _LOGGER.error("Failed to fetch live data stream from National Hurricane Center: %s", err)


class NHCChildTemplateSensor(SensorEntity):
    """The downstream child sensors listening for changes on sensor.nhc_storm_data."""

    def __init__(self, name, unique_id, state_template, attribute_templates):
        """Initialize child slots."""
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = "mdi:weather-hurricane"
        self._state_template = state_template
        self._attribute_templates = attribute_templates
        self._attr_native_value = "unavailable"
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        """Register state tracker listener hooks when mounted."""
        @callback
        def _async_state_listener(event):
            """Force recalculation task execution when the parent data refreshes."""
            self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, ["sensor.nhc_storm_data"], _async_state_listener
            )
        )

    async def async_update(self) -> None:
        """Render templates dynamically based on parent entity updates."""
        try:
            parent_state = self.hass.states.get("sensor.nhc_storm_data")
            if not parent_state or not parent_state.attributes.get("activeStorms"):
                self._attr_native_value = "Waiting for data..."
                return

            self._attr_native_value = self._state_template.async_render(parse_result=True)
            
            rendered_attrs = {}
            for key, template_obj in self._attribute_templates.items():
                rendered_attrs[key] = template_obj.async_render(parse_result=True)
            self._attr_extra_state_attributes = rendered_attrs
            
        except Exception as err:
            _LOGGER.error("Error rendering template values for %s: %s", self._attr_name, err)

