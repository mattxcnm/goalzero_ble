"""Goal Zero Alta 80 device implementation."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from bleak import BleakClient
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature

from .base import GoalZeroDevice

_LOGGER = logging.getLogger(__name__)

# Alta 80 specific GATT handles (based on goalzero_gatt.py discovery)
ALTA80_WRITE_HANDLE = 0x000A
ALTA80_READ_HANDLE = 0x000C
ALTA80_STATUS_COMMAND = "FEFE03010200"


class Alta80Device(GoalZeroDevice):
    """Goal Zero Alta 80 fridge system device."""

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
                "key": "power_consumption",
                "name": "Power Consumption",
                "device_class": SensorDeviceClass.POWER,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfPower.WATT,
            },
            {
                "key": "fridge_temperature",
                "name": "Fridge Temperature",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfTemperature.CELSIUS,
            },
            {
                "key": "ambient_temperature",
                "name": "Ambient Temperature",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfTemperature.CELSIUS,
            },
            {
                "key": "compressor_status",
                "name": "Compressor Status",
                "device_class": None,
                "state_class": None,
                "unit": None,
            },
        ]

    async def update_data(self, ble_device) -> Dict[str, Any]:
        """Update device data from BLE connection using GATT handles."""
        try:
            # Connect to the device using BleakClient
            async with BleakClient(ble_device.address) as client:
                _LOGGER.debug("Connected to Alta 80 device at %s", ble_device.address)
                
                # Find characteristics by handle
                write_char = None
                read_char = None
                
                services = client.services
                for service in services.services.values():
                    for char in service.characteristics:
                        if char.handle == ALTA80_WRITE_HANDLE:
                            write_char = char
                        if char.handle == ALTA80_READ_HANDLE:
                            read_char = char
                
                if not write_char or not read_char:
                    _LOGGER.error(
                        "Required characteristics not found. Write: %s, Read: %s",
                        write_char is not None,
                        read_char is not None
                    )
                    return self._data
                
                # Set up response collection
                responses = []
                response_count = 0
                
                def notification_handler(sender, data):
                    nonlocal response_count, responses
                    response_count += 1
                    hex_data = data.hex().upper()
                    _LOGGER.debug("Alta 80 Response %d: %s", response_count, hex_data)
                    responses.append(hex_data)
                
                # Start notifications
                await client.start_notify(read_char, notification_handler)
                
                # Send status request command
                command_bytes = bytes.fromhex(ALTA80_STATUS_COMMAND)
                await client.write_gatt_char(write_char, command_bytes)
                _LOGGER.debug("Sent status command: %s", ALTA80_STATUS_COMMAND)
                
                # Wait for responses (expecting 2 responses based on template)
                timeout = 10
                elapsed = 0
                while response_count < 2 and elapsed < timeout:
                    await asyncio.sleep(0.1)
                    elapsed += 0.1
                
                # Stop notifications
                await client.stop_notify(read_char)
                
                # Parse responses and update data
                if responses:
                    self._data = self._parse_gatt_responses(responses)
                    _LOGGER.debug("Updated Alta 80 data: %s", self._data)
                else:
                    _LOGGER.warning("No responses received from Alta 80 device")
                
        except Exception as e:
            _LOGGER.error("Error updating Alta 80 data: %s", e)
        
        return self._data

    async def send_control_command(self, command_hex: str) -> bool:
        """Send a control command to the Alta 80 device."""
        try:
            # This would be used by button entities for controlling the fridge
            async with BleakClient(self.address) as client:
                _LOGGER.debug("Sending control command to Alta 80: %s", command_hex)
                
                # Find write characteristic by handle
                write_char = None
                services = client.services
                for service in services.services.values():
                    for char in service.characteristics:
                        if char.handle == ALTA80_WRITE_HANDLE:
                            write_char = char
                            break
                
                if not write_char:
                    _LOGGER.error("Write characteristic not found for control command")
                    return False
                
                # Send command
                command_bytes = bytes.fromhex(command_hex)
                await client.write_gatt_char(write_char, command_bytes)
                _LOGGER.debug("Control command sent successfully")
                return True
                
        except Exception as e:
            _LOGGER.error("Error sending control command: %s", e)
            return False

    def _parse_gatt_responses(self, responses: list[str]) -> Dict[str, Any]:
        """Parse GATT responses from Alta 80 device."""
        parsed_data = {
            "battery_percentage": None,
            "power_consumption": None,
            "fridge_temperature": None,
            "ambient_temperature": None,
            "compressor_status": "unknown",
        }
        
        try:
            for response in responses:
                # Convert hex string to bytes for parsing
                data = bytes.fromhex(response)
                
                # Parse based on response format (this will need adjustment based on actual protocol)
                if len(data) >= 8:
                    # Example parsing - adjust based on actual Alta 80 protocol
                    # Response format analysis needed from actual device testing
                    
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

    def parse_ble_data(self, data: bytes) -> Dict[str, Any]:
        """Parse BLE data specific to Alta 80 fridge system."""
        # Convert single data packet to hex string format for consistency
        hex_data = data.hex().upper()
        return self._parse_gatt_responses([hex_data])
