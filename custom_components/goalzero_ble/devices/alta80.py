"""Goal Zero Alta 80 device implementation."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfIlluminance

from .base import GoalZeroDevice

_LOGGER = logging.getLogger(__name__)


class Alta80Device(GoalZeroDevice):
    """Goal Zero Alta 80 solar light tower device."""

    @property
    def device_type(self) -> str:
        """Return the device type identifier."""
        return "alta80"

    @property
    def model(self) -> str:
        """Return the device model name."""
        return "Alta 80"

    def get_sensors(self) -> list[dict[str, Any]]:
        """Return list of sensor definitions for this device."""
        return [
            {
                "key": "battery_percentage",
                "name": "Battery",
                "device_class": SensorDeviceClass.BATTERY,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": PERCENTAGE,
            },
            {
                "key": "solar_power",
                "name": "Solar Power",
                "device_class": SensorDeviceClass.POWER,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfPower.WATT,
            },
            {
                "key": "light_output",
                "name": "Light Output",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfIlluminance.LUX,
            },
            {
                "key": "light_brightness",
                "name": "Light Brightness",
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": PERCENTAGE,
            },
        ]

    async def update_data(self, ble_device) -> Dict[str, Any]:
        """Update device data from BLE connection."""
        # TODO: Implement actual BLE communication for Alta 80
        # This is a placeholder for the BLE protocol implementation
        
        # Example data structure - replace with actual BLE parsing
        self._data = {
            "battery_percentage": 72,   # Parse from BLE data
            "solar_power": 25,          # Parse from BLE data
            "light_output": 1200,       # Parse from BLE data
            "light_brightness": 80,     # Parse from BLE data
        }
        
        return self._data

    def parse_ble_data(self, data: bytes) -> Dict[str, Any]:
        """Parse BLE data specific to Alta 80."""
        # TODO: Implement Alta 80 specific BLE data parsing
        # This will depend on the actual BLE protocol used by the device
        parsed_data = {}
        
        # Placeholder parsing logic
        if len(data) >= 8:
            # Example: different byte structure than Yeti 500
            parsed_data["battery_percentage"] = data[0] if data[0] <= 100 else None
            parsed_data["light_brightness"] = data[1] if data[1] <= 100 else None
            # Add more parsing logic based on Alta 80 BLE protocol
        
        return parsed_data
