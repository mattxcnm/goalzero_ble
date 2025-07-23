"""Sensor platform for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME, PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Goal Zero BLE sensor based on a config entry."""
    address = config_entry.data[CONF_ADDRESS]
    name = config_entry.data[CONF_NAME]

    sensors = [
        GoalZeroBatteryPercentageSensor(address, name),
        GoalZeroPowerSensor(address, name),
    ]

    async_add_entities(sensors)


class GoalZeroBLESensorBase(SensorEntity):
    """Base class for Goal Zero BLE sensors."""

    def __init__(self, address: str, device_name: str) -> None:
        """Initialize the sensor."""
        self._address = address
        self._device_name = device_name
        self._attr_unique_id = f"{address}_{self.entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=device_name,
            manufacturer=MANUFACTURER,
            via_device=(DOMAIN, address),
        )


class GoalZeroBatteryPercentageSensor(GoalZeroBLESensorBase):
    """Battery percentage sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Battery"

    def __init__(self, address: str, device_name: str) -> None:
        """Initialize the battery sensor."""
        self.entity_description = type('EntityDescription', (), {
            'key': 'battery_percentage'
        })()
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
