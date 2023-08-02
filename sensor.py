import json
from homeassistant.helpers.entity import Entity
from homeassistant.components import mqtt
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Awtrix devices."""

    topic = config['state_topic']
    name = config['name']

    sensors = [
        CustomSensor('app', name, topic, 'app'),
        CustomSensor('wifi_signal', name, topic, 'wifi_signal'),
        CustomSensor('uptime', name, topic, 'uptime'),
        CustomSensor('ram', name, topic, 'ram'),
        CustomSensor('bat', name, topic, 'bat'),
        CustomSensor('lux', name, topic, 'lux'),
        CustomSensor('version', name, topic, 'version'),
    ]

    async_add_entities(sensors)

class CustomSensor(Entity):
    def __init__(self, id, device_name, topic, attr):
        """Initialize the sensor."""
        self._state = None
        self._attr = attr
        self._name = f"{device_name} {id}"
        self._topic = f"{topic}stats"

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
