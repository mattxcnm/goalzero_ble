"""Switch platform for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Goal Zero BLE switches."""
    coordinator: GoalZeroCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Get switch definitions from device
    device = coordinator.device
    if hasattr(device, 'get_switches'):
        switch_definitions = device.get_switches()
        
        for switch_def in switch_definitions:
            entities.append(
                GoalZeroSwitch(
                    coordinator,
                    switch_def["key"],
                    switch_def["name"],
                    switch_def.get("icon"),
                )
            )
    
    if entities:
        async_add_entities(entities, update_before_add=True)


class GoalZeroSwitch(GoalZeroEntity, SwitchEntity):
    """Goal Zero BLE switch."""

    def __init__(
        self,
        coordinator: GoalZeroCoordinator,
        key: str,
        name: str,
        icon: str | None,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, key, name, icon)

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        if self.coordinator.data:
            if self._key == "power":
                # Determine power state from device data
                # This might need to be adjusted based on actual device behavior
                return self.coordinator.data.get("power_on", False)
            elif self._key == "eco_mode":
                return self.coordinator.data.get("eco_mode", False)
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        try:
            device = self.coordinator.device
            if hasattr(device, 'create_switch_command'):
                command = device.create_switch_command(self._key, True)
                ble_manager = self.coordinator.ble_manager
                success = await device.send_command(ble_manager, command)
                
                if success:
                    await self.coordinator.async_request_refresh()
                    _LOGGER.info("Successfully turned on %s", self._key)
                else:
                    _LOGGER.error("Failed to turn on %s", self._key)
            else:
                _LOGGER.error("Device does not support switch commands")
                
        except Exception as e:
            _LOGGER.error("Error turning on switch %s: %s", self._key, e)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        try:
            device = self.coordinator.device
            if hasattr(device, 'create_switch_command'):
                command = device.create_switch_command(self._key, False)
                ble_manager = self.coordinator.ble_manager
                success = await device.send_command(ble_manager, command)
                
                if success:
                    await self.coordinator.async_request_refresh()
                    _LOGGER.info("Successfully turned off %s", self._key)
                else:
                    _LOGGER.error("Failed to turn off %s", self._key)
            else:
                _LOGGER.error("Device does not support switch commands")
                
        except Exception as e:
            _LOGGER.error("Error turning off switch %s: %s", self._key, e)
