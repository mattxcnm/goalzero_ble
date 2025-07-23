"""Sensor platform for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, ALTA_80
from .coordinator import GoalZeroCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Goal Zero BLE sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        GoalZeroRawDataSensor(coordinator, config_entry),
        GoalZeroLeftZoneSensor(coordinator, config_entry),
        GoalZeroRightZoneSensor(coordinator, config_entry),
    ]

    async_add_entities(entities)


class GoalZeroBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for Goal Zero devices."""

    def __init__(self, coordinator: GoalZeroCoordinator, config_entry: ConfigEntry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": f"{ALTA_80} ({coordinator.mac_address})",
            "manufacturer": MANUFACTURER,
            "model": ALTA_80,
        }


class GoalZeroRawDataSensor(GoalZeroBaseSensor):
    """Raw data sensor."""

    def __init__(self, coordinator: GoalZeroCoordinator, config_entry: ConfigEntry):
        """Initialize the raw data sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{coordinator.mac_address}_raw_data"
        self._attr_name = f"{ALTA_80} Raw Data"
        self._attr_icon = "mdi:code-string"

    @property
    def native_value(self):
        """Return the raw data."""
        if self.coordinator.data:
            return self.coordinator.data.get("raw_data", "")
        return ""


class GoalZeroLeftZoneSensor(GoalZeroBaseSensor):
    """Left zone temperature sensor."""

    def __init__(self, coordinator: GoalZeroCoordinator, config_entry: ConfigEntry):
        """Initialize the left zone sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{coordinator.mac_address}_left_zone_temp"
        self._attr_name = f"{ALTA_80} Left Zone Temperature"
        self._attr_native_unit_of_measurement = "°F"
        self._attr_device_class = "temperature"
        self._attr_icon = "mdi:thermometer"

    @property
    def native_value(self):
        """Return the left zone temperature."""
        # TODO: Decode from raw data once protocol is known
        return None


class GoalZeroRightZoneSensor(GoalZeroBaseSensor):
    """Right zone temperature sensor."""

    def __init__(self, coordinator: GoalZeroCoordinator, config_entry: ConfigEntry):
        """Initialize the right zone sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{coordinator.mac_address}_right_zone_temp"
        self._attr_name = f"{ALTA_80} Right Zone Temperature"
        self._attr_native_unit_of_measurement = "°F"
        self._attr_device_class = "temperature"
        self._attr_icon = "mdi:thermometer"

    @property
    def native_value(self):
        """Return the right zone temperature."""
        # TODO: Decode from raw data once protocol is known
        return None
