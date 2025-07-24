"""Base Goal Zero device class."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


class GoalZeroDevice(ABC):
    """Base class for Goal Zero devices."""

    def __init__(self, address: str, name: str) -> None:
        """Initialize the device."""
        self.address = address
        self.name = name
        self._data: dict[str, Any] = {}

    @property
    @abstractmethod
    def device_type(self) -> str:
        """Return the device type identifier."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Return the device model name."""

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.address)},
            name=self.name,
            manufacturer=MANUFACTURER,
            model=self.model,
            via_device=(DOMAIN, self.address),
        )

    @abstractmethod
    def get_sensors(self) -> list[dict[str, Any]]:
        """Return list of sensor definitions for this device."""

    @abstractmethod
    def get_buttons(self) -> list[dict[str, Any]]:
        """Return list of button definitions for this device."""

    @abstractmethod
    async def update_data(self, ble_manager) -> dict[str, Any]:
        """Update device data from BLE connection."""

    def get_sensor_value(self, sensor_key: str, data: dict[str, Any] | None = None) -> Any:
        """Get current sensor value."""
        if data is None:
            data = self._data
        return data.get(sensor_key)

    def parse_ble_data(self, data: bytes) -> dict[str, Any]:
        """Parse BLE data into sensor values."""
        # Default implementation - override in device classes
        return {}

    async def send_button_command(self, ble_manager, button_key: str) -> bool:
        """Send a button command via BLE manager."""
        from ..device_registry import DeviceRegistry
        
        commands = DeviceRegistry.get_device_commands(self.device_type)
        if button_key not in commands:
            _LOGGER.error("Command %s not available for device type %s", button_key, self.device_type)
            return False
        
        command_hex = commands[button_key]
        return await ble_manager.send_command(command_hex)
