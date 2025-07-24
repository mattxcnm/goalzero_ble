"""Goal Zero Alta 80 device implementation."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature

from .base import GoalZeroDevice
from ..const import DEVICE_TYPE_ALTA80, ALTA_80_MODEL

_LOGGER = logging.getLogger(__name__)


class Alta80Device(GoalZeroDevice):
    """Goal Zero Alta 80 fridge system device."""

    @property
    def device_type(self) -> str:
        """Return the device type identifier."""
        return DEVICE_TYPE_ALTA80

    @property
    def model(self) -> str:
        """Return the device model name."""
        return ALTA_80_MODEL

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
                "key": "power_consumption",
                "name": "Power Consumption",
                "device_class": SensorDeviceClass.POWER,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfPower.WATT,
                "icon": "mdi:lightning-bolt",
            },
            {
                "key": "fridge_temperature",
                "name": "Fridge Temperature",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfTemperature.CELSIUS,
                "icon": "mdi:thermometer",
            },
            {
                "key": "ambient_temperature",
                "name": "Ambient Temperature",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfTemperature.CELSIUS,
                "icon": "mdi:thermometer-lines",
            },
            {
                "key": "compressor_status",
                "name": "Compressor Status",
                "device_class": None,
                "state_class": None,
                "unit": None,
                "icon": "mdi:hvac",
            },
        ]

    def get_buttons(self) -> list[dict[str, Any]]:
        """Return list of button definitions for this device."""
        return [
            {
                "key": "temp_up",
                "name": "Temperature Up",
                "icon": "mdi:thermometer-plus",
            },
            {
                "key": "temp_down",
                "name": "Temperature Down",
                "icon": "mdi:thermometer-minus",
            },
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
            {
                "key": "eco_on",
                "name": "Eco Mode On",
                "icon": "mdi:leaf",
            },
            {
                "key": "eco_off",
                "name": "Eco Mode Off",
                "icon": "mdi:leaf-off",
            },
        ]

    async def update_data(self, ble_manager) -> dict[str, Any]:
        """Update device data from BLE connection using GATT handles."""
        try:
            _LOGGER.debug("Updating Alta 80 data via BLE manager")
            
            # Request status from device
            responses = await ble_manager.send_command_and_collect_responses(
                "FEFE03010200",  # Status request command
                expected_responses=2,
                timeout=10
            )
            
            if responses:
                self._data = self._parse_gatt_responses(responses)
                _LOGGER.debug("Updated Alta 80 data: %s", self._data)
            else:
                _LOGGER.warning("No responses received from Alta 80 device")
                # Return existing data if no new data received
                if not self._data:
                    self._data = self._get_default_data()
                
        except Exception as e:
            _LOGGER.error("Error updating Alta 80 data: %s", e)
            if not self._data:
                self._data = self._get_default_data()
        
        return self._data

    def _get_default_data(self) -> dict[str, Any]:
        """Return default data structure with None values."""
        return {
            "battery_percentage": None,
            "power_consumption": None,
            "fridge_temperature": None,
            "ambient_temperature": None,
            "compressor_status": "unknown",
        }

    def _parse_gatt_responses(self, responses: list[str]) -> dict[str, Any]:
        """Parse GATT responses from Alta 80 device."""
        parsed_data = self._get_default_data()
        
        try:
            for response in responses:
                # Convert hex string to bytes for parsing
                data = bytes.fromhex(response)
                
                # Parse based on response format (adjust based on actual Alta 80 protocol)
                if len(data) >= 8:
                    # Battery percentage (assuming byte 3)
                    if len(data) > 3:
                        battery_raw = data[3]
                        if 0 <= battery_raw <= 100:
                            parsed_data["battery_percentage"] = battery_raw
                    
                    # Temperatures (assuming 16-bit little endian values)
                    if len(data) > 5:
                        fridge_temp_raw = int.from_bytes(data[4:6], 'little', signed=True)
                        parsed_data["fridge_temperature"] = fridge_temp_raw / 10.0
                    
                    if len(data) > 7:
                        ambient_temp_raw = int.from_bytes(data[6:8], 'little', signed=True)
                        parsed_data["ambient_temperature"] = ambient_temp_raw / 10.0
                    
                    # Power consumption (assuming bytes 8-9)
                    if len(data) > 9:
                        power_raw = int.from_bytes(data[8:10], 'little')
                        parsed_data["power_consumption"] = power_raw
                    
                    # Compressor status (assuming bit flag in byte 10)
                    if len(data) > 10:
                        status_flags = data[10]
                        if status_flags & 0x01:
                            parsed_data["compressor_status"] = "running"
                        elif status_flags & 0x02:
                            parsed_data["compressor_status"] = "cooling"
                        else:
                            parsed_data["compressor_status"] = "off"
                
        except Exception as e:
            _LOGGER.error("Error parsing GATT responses: %s", e)
        
        return parsed_data

    def parse_ble_data(self, data: bytes) -> dict[str, Any]:
        """Parse BLE data specific to Alta 80 fridge system."""
        # Convert single data packet to hex string format for consistency
        hex_data = data.hex().upper()
        return self._parse_gatt_responses([hex_data])
