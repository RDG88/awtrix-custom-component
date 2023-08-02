import json
from homeassistant.helpers.entity import Entity
from homeassistant.components import mqtt
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Awtrix devices."""

    config = config_entry.data

    topic = config['host']
    # name = config['name']
    name = config['host']

    sensors = [
        CustomSensor('app', name, topic, 'app', device_class='battery'),
        CustomSensor('wifi_signal', name, topic, 'wifi_signal', device_class='signal_strength', state_class='signal_strength', unit_of_measurement='dBm', icon='mdi:sun-wireless'),
        CustomSensor('uptime', name, topic, 'uptime'),
        CustomSensor('ram', name, topic, 'ram', device_class='memory', state_class='data_size',unit_of_measurement='B', icon='mdi:memory'),
        CustomSensor('bat', name, topic, 'bat', device_class='battery'),
        CustomSensor('lux', name, topic, 'lux', device_class='illuminance'),
        CustomSensor('version', name, topic, 'version'),
    ]

    async_add_entities(sensors)

class CustomSensor(Entity):
    def __init__(self, id, device_name, topic, attr, device_class=None, state_class=None, unit_of_measurement=None, icon=None):
        """Initialize the sensor."""
        self._state = None
        self._attr = attr
        self._name = f"{device_name} {id}"
        self._topic = f"{topic}/stats"
        self._device_class = device_class
        self._state_class = state_class
        self._unit_of_measurement = unit_of_measurement
        self._icon = icon


    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        await super().async_added_to_hass()

        self.async_on_remove(
            await mqtt.async_subscribe(
                self.hass,
                self._topic,
                self._message_received,
                1,
                None,
            )
        )
        _LOGGER.warning("Trying to read from MQTT topic %s", self._topic)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return self._state_class
    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return self._unit_of_measurement
    @property
    def state_attributes(self):
        """Return the state attributes."""
        return {"device_class": self._device_class}
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def _message_received(self, msg):
        """Handle new MQTT messages."""
        data = json.loads(msg.payload)
        if self._attr in data:
            self._state = data[self._attr]
            self.async_write_ha_state()
            _LOGGER.warning("Received an update for %s from MQTT topic %s. New state is %s", self._name, self._topic, self._state)

