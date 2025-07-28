"""Device registry for Goal Zero BLE devices."""
from __future__ import annotations

import logging
import re
from typing import Any

from .const import (
    ALTA_PATTERN,
    YETI500_PATTERN,
    DEVICE_TYPE_ALTA80,
    DEVICE_TYPE_YETI500,
    ALTA_80_MODEL,
    YETI_500_MODEL,
    DEVICE_COMMANDS,
    DEVICE_HANDLES,
)
from .devices.alta80 import Alta80Device
from .devices.yeti500 import Yeti500Device

_LOGGER = logging.getLogger(__name__)


class DeviceRegistry:
    """Registry for Goal Zero device types and configurations."""

    _DEVICE_PATTERNS = {
        DEVICE_TYPE_ALTA80: re.compile(r"^gzf1-80-[A-F0-9]{6}$", re.IGNORECASE),
        DEVICE_TYPE_YETI500: re.compile(r"^gzy5c-[A-F0-9]{6}$", re.IGNORECASE),
    }

    _DEVICE_CLASSES = {
        DEVICE_TYPE_ALTA80: Alta80Device,
        DEVICE_TYPE_YETI500: Yeti500Device,
    }

    _DEVICE_MODELS = {
        DEVICE_TYPE_ALTA80: ALTA_80_MODEL,
        DEVICE_TYPE_YETI500: YETI_500_MODEL,
    }

    @classmethod
    def detect_device_type(cls, device_name: str) -> str | None:
        """Detect device type from BLE device name."""
        if not device_name:
            return None

        device_name = device_name.strip()
        
        for device_type, pattern in cls._DEVICE_PATTERNS.items():
            if pattern.match(device_name):
                _LOGGER.debug("Detected device type %s for name %s", device_type, device_name)
                return device_type

        _LOGGER.debug("No matching device type found for name: %s", device_name)
        return None

    @classmethod
    def is_supported_device(cls, device_name: str) -> bool:
        """Check if a device name matches supported patterns."""
        return cls.detect_device_type(device_name) is not None

    @classmethod
    def create_device(cls, device_type: str, address: str, name: str) -> Any | None:
        """Create a device instance based on detected type."""
        device_class = cls._DEVICE_CLASSES.get(device_type)
        if device_class:
            _LOGGER.debug("Creating device instance for type %s", device_type)
            return device_class(address, name)
        
        _LOGGER.error("No device class found for type: %s", device_type)
        return None

    @classmethod
    def get_device_model(cls, device_type: str) -> str:
        """Get the model name for a device type."""
        return cls._DEVICE_MODELS.get(device_type, "Unknown Goal Zero Device")

    @classmethod
    def get_device_commands(cls, device_type: str) -> dict[str, str]:
        """Get available commands for a device type."""
        return DEVICE_COMMANDS.get(device_type, {})

    @classmethod
    def get_device_handles(cls, device_type: str) -> dict[str, int]:
        """Get GATT handles for a device type."""
        return DEVICE_HANDLES.get(device_type, {})

    @classmethod
    def get_supported_device_types(cls) -> list[str]:
        """Get list of all supported device types."""
        return list(cls._DEVICE_CLASSES.keys())

    @classmethod
    def get_device_patterns(cls) -> dict[str, str]:
        """Get device name patterns for documentation/debugging."""
        return {
            device_type: pattern.pattern 
            for device_type, pattern in cls._DEVICE_PATTERNS.items()
        }
