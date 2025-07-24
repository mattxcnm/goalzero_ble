"""Data coordinator for Goal Zero BLE integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_DEVICE_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    BLE_COMMAND_TIMEOUT,
    DEVICE_TYPE_ALTA80,
)
from .device_registry import DeviceRegistry
from .ble_manager import GoalZeroBLEManager

_LOGGER = logging.getLogger(__name__)


class GoalZeroCoordinator(DataUpdateCoordinator):
    """Data coordinator for Goal Zero devices."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        self.device_name = config_entry.data[CONF_DEVICE_NAME]
        self.address = config_entry.data["address"]
        self.device_type = config_entry.data["device_type"]
        
        update_interval = config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.device_name}",
            update_interval=timedelta(seconds=update_interval),
        )
        
        # Create device instance
        self.device = DeviceRegistry.create_device(
            self.device_type, self.address, self.device_name
        )
        
        if not self.device:
            raise ValueError(f"Failed to create device for type: {self.device_type}")
        
        # Initialize BLE manager
        self.ble_manager = GoalZeroBLEManager(self.address, self.device_type)
        
        # Track GATT discovery for debugging
        self._gatt_discovery_done = False
        
        # Flag to track if we've done GATT discovery for debugging
        self._gatt_discovery_done = False
        
        _LOGGER.info(
            "Initialized coordinator for %s (%s) at %s with %ds update interval",
            self.device_name,
            self.device_type,
            self.address,
            update_interval
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from the device."""
        try:
            _LOGGER.debug("Updating data for %s", self.device_name)
            
            # For Alta 80, we connect, get data, then disconnect each time
            # This follows the pattern from goalzero_gatt.py
            if self.device_type == DEVICE_TYPE_ALTA80:
                # Direct device update - device handles its own connection
                data = await self.device.update_data(None)
            else:
                # For other devices, use the BLE manager
                if not await self.ble_manager.ensure_connected():
                    raise UpdateFailed(f"Failed to connect to {self.device_name}")
                
                data = await self.device.update_data(self.ble_manager)
            
            if data is None:
                # If no data and we haven't done GATT discovery, try it for debugging
                if not self._gatt_discovery_done and self.device_type != DEVICE_TYPE_ALTA80:
                    _LOGGER.info("Attempting GATT discovery for debugging %s", self.device_name)
                    if await self.ble_manager.ensure_connected():
                        await self.ble_manager.discover_gatt_services()
                        self._gatt_discovery_done = True
                
                raise UpdateFailed(f"No data received from {self.device_name}")
            
            _LOGGER.debug("Successfully updated data for %s: %d keys", self.device_name, len(data))
            return data
            
        except Exception as e:
            _LOGGER.error("Error updating data for %s: %s", self.device_name, e)
            # Don't disconnect on temporary errors to avoid connection churn for non-Alta80 devices
            raise UpdateFailed(f"Error updating {self.device_name}: {e}") from e

    async def send_command(self, command_key: str) -> bool:
        """Send a predefined command to the device."""
        try:
            commands = DeviceRegistry.get_device_commands(self.device_type)
            if command_key not in commands:
                _LOGGER.error("Command %s not available for device type %s", command_key, self.device_type)
                return False
            
            command_hex = commands[command_key]
            return await self.send_custom_command(command_hex)
            
        except Exception as e:
            _LOGGER.error("Error sending command %s to %s: %s", command_key, self.device_name, e)
            return False

    async def send_custom_command(self, command_hex: str) -> bool:
        """Send a custom hex command to the device."""
        try:
            _LOGGER.debug("Sending custom command to %s: %s", self.device_name, command_hex)
            
            if not await self.ble_manager.ensure_connected():
                _LOGGER.error("Failed to connect to %s for command", self.device_name)
                return False
            
            success = await self.ble_manager.send_command(command_hex)
            
            if success:
                _LOGGER.debug("Successfully sent command to %s", self.device_name)
                # Trigger a data update after command to get latest status
                await self.async_request_refresh()
            else:
                _LOGGER.error("Failed to send command to %s", self.device_name)
            
            return success
            
        except Exception as e:
            _LOGGER.error("Error sending custom command to %s: %s", self.device_name, e)
            return False

    def get_sensor_value(self, sensor_key: str):
        """Get current sensor value."""
        if self.data and self.device:
            return self.device.get_sensor_value(sensor_key, self.data)
        return None

    async def async_shutdown(self) -> None:
        """Clean shutdown of the coordinator."""
        _LOGGER.debug("Shutting down coordinator for %s", self.device_name)
        if self.ble_manager:
            await self.ble_manager.disconnect()

    @property
    def device_info(self):
        """Return device information."""
        if self.device:
            return self.device.device_info
        return None

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self.ble_manager.is_connected if self.ble_manager else False
