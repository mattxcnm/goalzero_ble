"""Goal Zero Yeti 500 device implementation."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfElectricCurrent, UnitOfElectricPotential

from .base import GoalZeroDevice
from ..const import DEVICE_TYPE_YETI500, YETI_500_MODEL

_LOGGER = logging.getLogger(__name__)


class Yeti500Device(GoalZeroDevice):
    """Goal Zero Yeti 500 power station device."""

    @property
    def device_type(self) -> str:
        """Return the device type identifier."""
        return DEVICE_TYPE_YETI500

    @property
    def model(self) -> str:
        """Return the device model name."""
        return YETI_500_MODEL

    def get_sensors(self) -> list[dict[str, Any]]:
        """Return list of sensor definitions for this device."""
        return [
            {
                "key": "battery_percentage",
                "name": "Battery",
                "device_class": SensorDeviceClass.BATTERY,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": PERCENTAGE,
                "icon": "mdi:battery",
            },
            {
                "key": "power_out",
                "name": "Power Output",
                "device_class": SensorDeviceClass.POWER,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfPower.WATT,
                "icon": "mdi:lightning-bolt",
            },
            {
                "key": "power_in",
                "name": "Power Input",
                "device_class": SensorDeviceClass.POWER,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfPower.WATT,
                "icon": "mdi:lightning-bolt-outline",
            },
            {
                "key": "voltage",
                "name": "Voltage",
                "device_class": SensorDeviceClass.VOLTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfElectricPotential.VOLT,
                "icon": "mdi:flash",
            },
            {
                "key": "current",
                "name": "Current",
                "device_class": SensorDeviceClass.CURRENT,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfElectricCurrent.AMPERE,
                "icon": "mdi:current-ac",
            },
        ]

    def get_buttons(self) -> list[dict[str, Any]]:
        """Return list of button definitions for this device."""
        return [
            {
                "key": "power_on",
                "name": "Power On",
                "icon": "mdi:power",
            },
            {
                "key": "power_off",
                "name": "Power Off",
                "icon": "mdi:power-off",
            },
        ]

    async def update_data(self, ble_manager) -> dict[str, Any]:
        """Update device data from BLE connection."""
        try:
            _LOGGER.debug("Updating Yeti 500 data via BLE manager")
            
            # Request status from device (command to be verified with actual device)
            responses = await ble_manager.send_command_and_collect_responses(
                "FEFE03010200",  # Status request command (placeholder)
                expected_responses=2,
                timeout=10
            )
            
            if responses:
                self._data = self._parse_gatt_responses(responses)
                _LOGGER.debug("Updated Yeti 500 data: %s", self._data)
            else:
                _LOGGER.warning("No responses received from Yeti 500 device")
                # Return existing data if no new data received
                if not self._data:
                    self._data = self._get_default_data()
                
        except Exception as e:
            _LOGGER.error("Error updating Yeti 500 data: %s", e)
            if not self._data:
                self._data = self._get_default_data()
        
        return self._data

    def _get_default_data(self) -> dict[str, Any]:
        """Return default data structure with None values."""
        return {
            "battery_percentage": None,
            "power_out": None,
            "power_in": None,
            "voltage": None,
            "current": None,
        }

    def _parse_gatt_responses(self, responses: list[str]) -> dict[str, Any]:
        """Parse GATT responses from Yeti 500 device."""
        parsed_data = self._get_default_data()
        
        try:
            for response in responses:
                # Convert hex string to bytes for parsing
                data = bytes.fromhex(response)
                
                # Parse based on response format (to be determined with actual device)
                if len(data) >= 8:
                    # Battery percentage (placeholder parsing)
                    if len(data) > 0:
                        battery_raw = data[0]
                        if 0 <= battery_raw <= 100:
                            parsed_data["battery_percentage"] = battery_raw
                    
                    # Power values (placeholder parsing - adjust based on actual protocol)
                    if len(data) > 4:
                        power_out_raw = int.from_bytes(data[2:4], 'little')
                        parsed_data["power_out"] = power_out_raw
                    
                    if len(data) > 6:
                        power_in_raw = int.from_bytes(data[4:6], 'little')
                        parsed_data["power_in"] = power_in_raw
                    
                    # Voltage and current (placeholder parsing)
                    if len(data) > 8:
                        voltage_raw = int.from_bytes(data[6:8], 'little')
                        parsed_data["voltage"] = voltage_raw / 100.0  # Assuming centivolt scale
                    
                    if len(data) > 10:
                        current_raw = int.from_bytes(data[8:10], 'little')
                        parsed_data["current"] = current_raw / 100.0  # Assuming centiamp scale
                
        except Exception as e:
            _LOGGER.error("Error parsing Yeti 500 GATT responses: %s", e)
        
        return parsed_data

    def parse_ble_data(self, data: bytes) -> dict[str, Any]:
        """Parse BLE data specific to Yeti 500."""
        # Convert single data packet to hex string format for consistency
        hex_data = data.hex().upper()
        return self._parse_gatt_responses([hex_data])
