"""Button platform for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
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
    """Set up Goal Zero BLE buttons."""
    coordinator: GoalZeroCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    if not coordinator.device:
        _LOGGER.error("No device found for coordinator")
        return

    # Get button definitions from device
    button_definitions = coordinator.device.get_buttons()
    
    # Create button entities
    entities = []
    for button_def in button_definitions:
        entities.append(GoalZeroButton(coordinator, button_def))
    
    _LOGGER.info("Setting up %d buttons for %s", len(entities), coordinator.device_name)
    async_add_entities(entities)


class GoalZeroButton(CoordinatorEntity, ButtonEntity):
    """Goal Zero BLE button."""

    def __init__(self, coordinator: GoalZeroCoordinator, button_definition: dict[str, Any]) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        
        self.coordinator = coordinator
        self.button_def = button_definition
        self._button_key = button_definition["key"]
        
        # Set up entity attributes
        self._attr_unique_id = f"{coordinator.address}_{self._button_key}"
        self._attr_name = f"{coordinator.device_name} {button_definition['name']}"
        self._attr_icon = button_definition.get("icon")
        
        # Device info
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        """Handle button press."""
        try:
            _LOGGER.debug("Button %s pressed for %s", self._button_key, self.coordinator.device_name)
            
            # Send command via coordinator
            success = await self.coordinator.send_command(self._button_key)
            
            if not success:
                _LOGGER.error("Failed to send command %s to %s", self._button_key, self.coordinator.device_name)
            else:
                _LOGGER.debug("Successfully sent command %s to %s", self._button_key, self.coordinator.device_name)
                
        except Exception as e:
            _LOGGER.error("Error pressing button %s: %s", self._button_key, e)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.is_connected

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        return {
            "device_type": self.coordinator.device_type,
            "command_key": self._button_key,
        }
