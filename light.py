import json
from homeassistant.components import mqtt
from homeassistant.components.light import LightEntity, ATTR_BRIGHTNESS, ATTR_RGB_COLOR, COLOR_MODE_RGB
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the custom light devices."""

    config = config_entry.data

    topic = config['host']
    name = config['host']

    lights = [
        CustomLight(
            name="Matrix",
            state_topic=f"{topic}/stats",
            command_topic=f"{topic}/power",
            color_topic=f"{topic}/settings",
            brightness_topic=f"{topic}/settings",
        ),
    ]

    async_add_entities(lights)

class CustomLight(LightEntity):
    def __init__(self, name, state_topic, command_topic, color_topic, brightness_topic):
        """Initialize the light."""
        self._state = None
        self._brightness = 255  # Set default brightness to maximum
        self._rgb_color = (255, 255, 255)  # Set default color to white
        self._name = name
        self._state_topic = state_topic
        self._command_topic = command_topic
        self._color_topic = color_topic
        self._brightness_topic = brightness_topic

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        await super().async_added_to_hass()

        self.async_on_remove(
            await mqtt.async_subscribe(
                self.hass,
                self._state_topic,
                self._message_received,
                1,
                None,
            )
        )
        _LOGGER.warning("Trying to read from MQTT topic %s", self._state_topic)

    @property
    def name(self):
        """Return the name of the light."""
        return self._name

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def rgb_color(self):
        """Return the RGB color value."""
        return self._rgb_color

    @property
    def supported_color_modes(self):
        """Return the list of supported color modes."""
        return [COLOR_MODE_RGB]

    @property
    def color_mode(self):
        """Return the current color mode."""
        return COLOR_MODE_RGB

    def _message_received(self, msg):
        """Handle new MQTT messages."""
        data = json.loads(msg.payload)
        if 'state' in data:
            self._state = data['state']
            self.async_write_ha_state()
            _LOGGER.warning("Received an update for %s from MQTT topic %s. New state is %s", self._name, self._topic, self._state)

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.warning("Brightness: %s", self._brightness)
            await mqtt.async_publish(self.hass, self._brightness_topic, json.dumps({"BRI": self._brightness}), qos=1)
        if ATTR_RGB_COLOR in kwargs:
            self._rgb_color = kwargs[ATTR_RGB_COLOR]
            await mqtt.async_publish(self.hass, self._color_topic, json.dumps({"TCOL": self._rgb_color}), qos=1)
        await mqtt.async_publish(self.hass, self._command_topic, json.dumps({"power": True}), qos=1)
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await mqtt.async_publish(self.hass, self._command_topic, json.dumps({"power": False}), qos=1)
        self._state = False
        self.async_write_ha_state()
