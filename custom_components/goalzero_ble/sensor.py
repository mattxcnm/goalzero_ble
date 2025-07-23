"""Sensor platform for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .devices import create_device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Goal Zero BLE sensor based on a config entry."""
    address = config_entry.data[CONF_ADDRESS]
    name = config_entry.data[CONF_NAME]
    device_type = config_entry.data.get("device_type", "yeti500")

    # Create device instance
    device = create_device(device_type, address, name)
    if not device:
        _LOGGER.error("Failed to create device for type: %s", device_type)
        return

    # Create sensors based on device capabilities
    sensors = []
    for sensor_def in device.get_sensors():
        sensors.append(GoalZeroBLESensor(device, sensor_def))

    async_add_entities(sensors)


class GoalZeroBLESensor(SensorEntity):
    """Goal Zero BLE sensor."""

    def __init__(self, device, sensor_def: dict[str, Any]) -> None:
        """Initialize the sensor."""
        self._device = device
        self._sensor_def = sensor_def
        self._attr_unique_id = f"{device.address}_{sensor_def['key']}"
        self._attr_name = f"{device.name} {sensor_def['name']}"
        self._attr_device_class = sensor_def.get("device_class")
        self._attr_state_class = sensor_def.get("state_class")
        self._attr_native_unit_of_measurement = sensor_def.get("unit")
        self._attr_device_info = device.device_info

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self._device.get_sensor_value(self._sensor_def["key"])

    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # TODO: Implement actual BLE connection and data update
            await self._device.update_data(None)
        except Exception as err:
            _LOGGER.error("Error updating %s: %s", self.name, err)
        super().__init__(address, device_name)


class GoalZeroPowerSensor(GoalZeroBLESensorBase):
    """Power sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_name = "Power"

    def __init__(self, address: str, device_name: str) -> None:
        """Initialize the power sensor."""
        self.entity_description = type('EntityDescription', (), {
            'key': 'power'
        })()
        super().__init__(address, device_name)
