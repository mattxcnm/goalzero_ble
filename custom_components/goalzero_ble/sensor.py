"""Sensor platform for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GoalZeroCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Goal Zero BLE sensors."""
    coordinator: GoalZeroCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    if not coordinator.device:
        _LOGGER.error("No device found for coordinator")
        return

    # Get sensor definitions from device
    sensor_definitions = coordinator.device.get_sensors()
    
    # Create sensor entities - filter out byte sensors that aren't being used
    entities = []
    for sensor_def in sensor_definitions:
        # For status byte sensors, only create them if they have data or are decoded sensors
        sensor_key = sensor_def["key"]
        if sensor_key.startswith("status_byte_"):
            # Only create byte sensors for the 36 bytes (0-35) 
            byte_num = int(sensor_key.split("_")[-1])
            if byte_num < 36:  # Exactly 36 bytes (0-35) in Alta 80 response
                entities.append(GoalZeroSensor(coordinator, sensor_def))
        else:
            # Always create non-byte sensors (decoded values, etc.)
            entities.append(GoalZeroSensor(coordinator, sensor_def))
    
    _LOGGER.info("Setting up %d sensors for %s", len(entities), coordinator.device_name)
    async_add_entities(entities)


class GoalZeroSensor(CoordinatorEntity, SensorEntity):
    """Goal Zero BLE sensor."""

    def __init__(self, coordinator: GoalZeroCoordinator, sensor_definition: dict[str, Any]) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self.coordinator = coordinator
        self.sensor_def = sensor_definition
        self._sensor_key = sensor_definition["key"]
        
        # Set up entity attributes
        self._attr_unique_id = f"{coordinator.address}_{self._sensor_key}"
        self._attr_name = f"{coordinator.device_name} {sensor_definition['name']}"
        self._attr_device_class = sensor_definition.get("device_class")
        self._attr_state_class = sensor_definition.get("state_class")
        self._attr_native_unit_of_measurement = sensor_definition.get("unit")
        self._attr_icon = sensor_definition.get("icon")
        
        # Device info
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        """Return the current value of the sensor."""
        return self.coordinator.get_sensor_value(self._sensor_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.is_connected

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        attrs = {
            "device_type": self.coordinator.device_type,
            "last_update": self.coordinator.last_update_success_time,
        }
        
        # Add raw sensor value if different from native_value
        raw_value = self.coordinator.get_sensor_value(self._sensor_key)
        if raw_value is not None:
            attrs["raw_value"] = raw_value
        
        # For byte sensors, add hex representation
        if self._sensor_key.startswith("status_byte_") and raw_value is not None:
            attrs["hex_value"] = f"0x{raw_value:02X}"
            
        # For concatenated response, add length info
        if self._sensor_key == "concatenated_response" and raw_value:
            attrs["response_length_chars"] = len(str(raw_value))
            attrs["response_length_bytes"] = len(str(raw_value)) // 2
            
        return attrs
