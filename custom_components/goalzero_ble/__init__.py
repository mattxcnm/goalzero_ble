"""Goal Zero BLE integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_DEVICE_NAME
from .coordinator import GoalZeroCoordinator
from .device_registry import DeviceRegistry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR, 
    Platform.BUTTON, 
    Platform.NUMBER, 
    Platform.SWITCH, 
    Platform.SELECT
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Goal Zero BLE from a config entry."""
    # Validate that we have all required data
    if CONF_ADDRESS not in entry.data or CONF_DEVICE_NAME not in entry.data:
        _LOGGER.error("Config entry missing required data: %s", entry.data)
        return False

    device_name = entry.data[CONF_DEVICE_NAME]
    address = entry.data[CONF_ADDRESS]
    
    _LOGGER.info("Setting up Goal Zero BLE integration for %s (%s)", device_name, address)
    
    # Verify device type is supported
    device_type = entry.data.get("device_type")
    if not device_type or device_type not in DeviceRegistry.get_supported_device_types():
        _LOGGER.error("Unsupported device type: %s", device_type)
        return False

    try:
        # Create coordinator
        coordinator = GoalZeroCoordinator(hass, entry)
        
        # Perform first refresh
        await coordinator.async_config_entry_first_refresh()
        
        # Store coordinator
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
        
        # Forward to platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        _LOGGER.info("Successfully set up Goal Zero BLE integration for %s", device_name)
        return True
        
    except Exception as e:
        _LOGGER.error("Failed to set up Goal Zero BLE integration for %s: %s", device_name, e)
        raise ConfigEntryNotReady(f"Failed to connect to {device_name}") from e


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    device_name = entry.data.get(CONF_DEVICE_NAME, "Unknown")
    _LOGGER.info("Unloading Goal Zero BLE integration for %s", device_name)
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Clean up coordinator
        coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
        if coordinator:
            await coordinator.async_shutdown()
        
        _LOGGER.info("Successfully unloaded Goal Zero BLE integration for %s", device_name)
    
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)
    
    if config_entry.version == 1:
        # No migration needed for version 1
        return True
    
    _LOGGER.error("Unknown configuration version %s", config_entry.version)
    return False
