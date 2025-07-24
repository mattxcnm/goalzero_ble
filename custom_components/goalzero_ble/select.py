"""Select platform for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
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
    """Set up Goal Zero BLE selects."""
    coordinator: GoalZeroCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Get select definitions from device
    device = coordinator.device
    if hasattr(device, 'get_selects'):
        select_definitions = device.get_selects()
        
        for select_def in select_definitions:
            entities.append(
                GoalZeroSelect(
                    coordinator,
                    select_def["key"],
                    select_def["name"],
                    select_def.get("icon"),
                    select_def["options"],
                )
            )
    
    if entities:
        async_add_entities(entities, update_before_add=True)


class GoalZeroSelect(GoalZeroEntity, SelectEntity):
    """Goal Zero BLE select."""

    def __init__(
        self,
        coordinator: GoalZeroCoordinator,
        key: str,
        name: str,
        icon: str | None,
        options: list[str],
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator, key, name, icon)
        self._attr_options = options

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        if self.coordinator.data:
            if self._key == "battery_protection":
                # Map internal value to display value
                raw_value = self.coordinator.data.get("battery_protection", "low")
                if isinstance(raw_value, str):
                    value_map = {
                        "low": "Low",
                        "med": "Medium", 
                        "medium": "Medium",
                        "high": "High"
                    }
                    return value_map.get(raw_value.lower(), "Low")
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            device = self.coordinator.device
            if hasattr(device, 'create_select_command'):
                # Map display value to internal value
                if self._key == "battery_protection":
                    option_map = {
                        "Low": "low",
                        "Medium": "med",
                        "High": "high"
                    }
                    internal_value = option_map.get(option, "low")
                else:
                    internal_value = option.lower()
                
                command = device.create_select_command(self._key, internal_value)
                ble_manager = self.coordinator.ble_manager
                success = await device.send_command(ble_manager, command)
                
                if success:
                    await self.coordinator.async_request_refresh()
                    _LOGGER.info("Successfully set %s to %s", self._key, option)
                else:
                    _LOGGER.error("Failed to set %s to %s", self._key, option)
            else:
                _LOGGER.error("Device does not support select commands")
                
        except Exception as e:
            _LOGGER.error("Error setting select %s to %s: %s", self._key, option, e)
