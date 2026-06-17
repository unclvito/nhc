import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.components.rest.sensor import RestSensor
from homeassistant.components.template.sensor import TemplateSensorEntity
from homeassistant.helpers.template import Template

_LOGGER = logging.getLogger(__name__)

SHARED_JINJA_MACROS = """
{% macro apply_markup(value, percent) %}
    {{ value | float(0) * (1 + (percent | float(0) / 100)) }}
{% endmacro %}

{% macro format_currency(value) %}
    ${{ "{:,.2f}".format(value | float(0)) }}
{% endmacro %}

{% macro get_state(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {% set winds = (storm['intensity'] if storm else 0|int*1.151)|round(2) %}
        {% if winds < 34 %}
            {% set intensity = 'TD' %}
        {% elif winds >= 34 and winds <= 73 %}
            {% set intensity = 'TS' %}
        {% elif winds >= 74 and winds <= 95 %}
            {% set intensity = 'Cat 1' %}
        {% elif winds >= 96 and winds <= 110 %}
            {% set intensity = 'Cat 2' %}
        {% elif winds >= 111 and winds <= 129 %}
            {% set intensity = 'Cat 3' %}
        {% elif winds >= 130 and winds <= 156 %}
            {% set intensity = 'Cat 4' %}
        {% elif winds >= 157 %}
            {% set intensity = 'Cat 5' %}
        {% else %}
            {% set intensity = winds ~ ' MPH' %}
        {% endif %}
        {{ storm['name'] }}, {{intensity }}
    {% else %}
        storm {{ binNumber }} unavailable
    {% endif %}
{% endmacro %}

{% macro get_name(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['name'] }}
    {% endif %}
{% endmacro %}

{% macro get_classification(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['classification'] }}
    {% endif %}
{% endmacro %}

{% macro get_pressure(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ (storm['pressure']|float/33.864)|round(2) }}
    {% endif %}
{% endmacro %}

{% macro get_intensity(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['intensity'] }}
    {% endif %}
{% endmacro %}

{% macro get_max_winds(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ (storm['intensity']|int*1.151)|round(2) }} MPH
    {% endif %}
{% endmacro %}

{% macro get_heading(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['movementDir'] }}
    {% endif %}
{% endmacro %}

{% macro get_heading_text(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {% set windbearing = ((storm['movementDir']|float(default=0)+22.5)/45)|int|round %}
        {% if windbearing > 7 %}{%  set windbearing = 0 %}{% endif %}
        {% set winddir = ['North', 'North East','East','South East','South','South West','West','North West'] %}
        {{ winddir[windbearing]|default('Unknown')}}
    {% endif %}
{% endmacro %}

{% macro get_movement_speed(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['movementSpeed'] }}
    {% endif %}
{% endmacro %}

{% macro get_distance(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ ((distance (storm['latitudeNumeric'], storm['longitudeNumeric'])))|round(2) }} miles
    {% endif %}
{% endmacro %}

{% macro get_latitude(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['latitudeNumeric'] }}
    {% endif %}
{% endmacro %}

{% macro get_longitude(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['longitudeNumeric'] }}
    {% endif %}
{% endmacro %}

{% macro get_region(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['binNumber'][:2] }}
    {% endif %}
{% endmacro %}

{% macro get_forecast_discussion(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['forecastDiscussion'].url }}
    {% endif %}
{% endmacro %}

{% macro get_forecast_graphics(binNumber) %}
    {% set storms = state_attr('sensor.nhc_storm_data','activeStorms') %}
    {% set stormsmatching = storms | selectattr('binNumber', 'eq', binNumber) %}
    {% if stormsmatching %}
        {% set storm = stormsmatching | first %}
        {{ storm['forecastGraphics'].url }}
    {% endif %}
{% endmacro %}
"""

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities,
    discovery_info: DiscoveryInfoType = None
) -> None:
    """Set up the REST and Template sensors programmatically."""

    # Create a REST platform sensor config
    rest_sensor_instance = RestSensor(
        hass=hass,
        resource="https://www.nhc.noaa.gov/CurrentStorms.json",
        auth=None,
        verify_ssl=True,
        name="NOAA NHC Current Storms REST",
        method="GET",
        payload=None,
        headers=None,
        params=None,
        timeout=10,
        value_template=hass.helpers.template.Template("{{ value_json.activeStorms | list | count  }}", hass),
        template_attributes=None,
        unit_of_measurement=None,
        device_class=None,
        state_class=None,
        json_attributes="activeStorms",
        scan_interval=180,
    )
    # CRITICAL: Force inject a unique ID into the REST entity class instance
    # This unlocks the UI settings gear icon for your users in Home Assistant
    rest_sensor_instance._attr_unique_id = "nhc_storm_data"

    # Create an empty storage array for our storm instances
    storm_entities = []

    # Configuration profiles map region names to their respective NHC basin prefix codes
    regions = {
        "Atlantic": "AT",
        "Eastern Pacific": "EP"
    }

    for region_name, prefix in regions.items():
        for i in range(1, 6):
            storm_code = f"{prefix}{i}"               # e.g., AT1, EP3
            unique_id_str = f"storm_{prefix.lower()}{i}" # e.g., storm_at1, storm_ep3
            display_name = f"{region_name} Storm {i}"   # e.g., Atlantic Storm 1, Eastern Pacific Storm 3

            storm_sensor = TemplateSensorEntity(
                hass=hass,
                config={
                    "name": display_name,
                    "unique_id": unique_id_str,
                    "state": Template(SHARED_JINJA_MACROS + f"{{{{ get_state('{storm_code}') }}}}", hass),
                    "icon": "mdi:weather-hurricane",
                    "attributes": {
                        "friendly_name": Template(SHARED_JINJA_MACROS + f"{{{{ get_classification('{storm_code}') }}}} {{{{ get_name('{storm_code}') }}}}", hass),
                        "storm_name": Template(SHARED_JINJA_MACROS + f"{{{{ get_name('{storm_code}') }}}}", hass),
                        "classification": Template(SHARED_JINJA_MACROS + f"{{{{ get_classification('{storm_code}') }}}}", hass),
                        "pressure": Template(SHARED_JINJA_MACROS + f"{{{{ get_pressure('{storm_code}') }}}}", hass),
                        "intensity": Template(SHARED_JINJA_MACROS + f"{{{{ get_intensity('{storm_code}') }}}}", hass),
                        "max_winds": Template(SHARED_JINJA_MACROS + f"{{{{ get_max_winds('{storm_code}') }}}}", hass),
                        "heading": Template(SHARED_JINJA_MACROS + f"{{{{ get_heading('{storm_code}') }}}}", hass),
                        "heading_text": Template(SHARED_JINJA_MACROS + f"{{{{ get_heading_text('{storm_code}') }}}}", hass),
                        "movement_speed": Template(SHARED_JINJA_MACROS + f"{{{{ get_movement_speed('{storm_code}') }}}}", hass),
                        "distance": Template(SHARED_JINJA_MACROS + f"{{{{ get_distance('{storm_code}') }}}}", hass),
                        "latitude": Template(SHARED_JINJA_MACROS + f"{{{{ get_latitude('{storm_code}') }}}}", hass),
                        "longitude": Template(SHARED_JINJA_MACROS + f"{{{{ get_longitude('{storm_code}') }}}}", hass),
                        "region": Template(SHARED_JINJA_MACROS + f"{{{{ get_region('{storm_code}') }}}}", hass),
                        "forecast_discussion": Template(SHARED_JINJA_MACROS + f"{{{{ get_forecast_discussion('{storm_code}') }}}}", hass),
                        "forecast_graphics": Template(SHARED_JINJA_MACROS + f"{{{{ get_forecast_graphics('{storm_code}') }}}}", hass),
                    }
                }
            )
            storm_entities.append(storm_sensor)

    # 3. Mass-push objects straight to registry
    async_add_entities([rest_sensor_instance] + storm_entities, update_before_add=True)

