"""Button platform for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GoalZeroCoordinator
from .entity import GoalZeroEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Goal Zero BLE buttons."""
    coordinator: GoalZeroCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Get button definitions from device
    device = coordinator.device
    if hasattr(device, 'get_buttons'):
        button_definitions = device.get_buttons()
        
        for button_def in button_definitions:
            entities.append(
                GoalZeroButton(
                    coordinator,
                    button_def["key"],
                    button_def["name"],
                    button_def.get("icon"),
                )
            )
    
    if entities:
        async_add_entities(entities, update_before_add=True)


class GoalZeroButton(GoalZeroEntity, ButtonEntity):
    """Goal Zero BLE button."""

    def __init__(
        self,
        coordinator: GoalZeroCoordinator,
        key: str,
        name: str,
        icon: str | None,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, key, name, icon)

    async def async_press(self) -> None:
        """Handle button press."""
        try:
            _LOGGER.debug("Button %s pressed", self._key)
            
            # Get current device data for context
            current_data = self.coordinator.data or {}
            
            # Create command for the button
            device = self.coordinator.device
            if hasattr(device, 'create_button_command'):
                command = device.create_button_command(
                    self._key,
                    current_temp=current_data.get("zone_1_temp", 32),  # Default to 32°F
                    current_eco_mode=current_data.get("eco_mode", False),
                    current_battery_protection=current_data.get("battery_protection", "low"),
                )
                
                # Send command via BLE manager
                ble_manager = self.coordinator.ble_manager
                success = await device.send_command(ble_manager, command)
                
                if success:
                    # Request a data refresh to get updated device state
                    await self.coordinator.async_request_refresh()
                    _LOGGER.info("Successfully executed button %s", self._key)
                else:
                    _LOGGER.error("Failed to execute button %s", self._key)
            else:
                _LOGGER.error("Device does not support button commands")
                
        except Exception as e:
            _LOGGER.error("Error pressing button %s: %s", self._key, e)
