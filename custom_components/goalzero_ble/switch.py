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
            # Check if there's a direct mapping for this switch key
            switch_value = self.coordinator.data.get(self._key)
            if switch_value is not None:
                return bool(switch_value)
            
            # Legacy mappings for backward compatibility
            if self._key == "power":
                return self.coordinator.data.get("power_on", False)
            elif self._key == "eco_mode":
                return self.coordinator.data.get("eco_mode", False)
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        _LOGGER.info("[SWITCH] User turning ON switch '%s'", self._key)
        try:
            device = self.coordinator.device
            ble_manager = self.coordinator.ble_manager
            _LOGGER.info("[SWITCH] Device type: %s", type(device).__name__)
            
            success = False
            
            # Check if device has set_switch_state method (for Yeti 500)
            if hasattr(device, 'set_switch_state'):
                _LOGGER.info("[SWITCH] Using set_switch_state method")
                success = await device.set_switch_state(ble_manager, self._key, True)
            
            # Fallback to create_switch_command method (for other devices)
            elif hasattr(device, 'create_switch_command'):
                _LOGGER.info("[SWITCH] Device has create_switch_command method")
                command = device.create_switch_command(self._key, True)
                _LOGGER.info("[SWITCH] Generated command: %s (%d bytes)", command.hex(':'), len(command))
                success = await device.send_command(ble_manager, command)
            else:
                _LOGGER.error("[SWITCH] Device does not support switch commands")
                return
                
            if success:
                _LOGGER.info("[SWITCH] Successfully turned on %s", self._key)
                # Request immediate refresh to update the state
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("[SWITCH] Failed to turn on %s", self._key)
                
        except Exception as e:
            _LOGGER.error("[SWITCH] Error turning on switch %s: %s", self._key, e)
            import traceback
            _LOGGER.error("[SWITCH] Traceback: %s", traceback.format_exc())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        _LOGGER.info("[SWITCH] User turning OFF switch '%s'", self._key)
        try:
            device = self.coordinator.device
            ble_manager = self.coordinator.ble_manager
            _LOGGER.info("[SWITCH] Device type: %s", type(device).__name__)
            
            success = False
            
            # Check if device has set_switch_state method (for Yeti 500)
            if hasattr(device, 'set_switch_state'):
                _LOGGER.info("[SWITCH] Using set_switch_state method")
                success = await device.set_switch_state(ble_manager, self._key, False)
            
            # Fallback to create_switch_command method (for other devices)
            elif hasattr(device, 'create_switch_command'):
                _LOGGER.info("[SWITCH] Device has create_switch_command method")
                command = device.create_switch_command(self._key, False)
                _LOGGER.info("[SWITCH] Generated command: %s (%d bytes)", command.hex(':'), len(command))
                success = await device.send_command(ble_manager, command)
            else:
                _LOGGER.error("[SWITCH] Device does not support switch commands")
                return
                
            if success:
                _LOGGER.info("[SWITCH] Successfully turned off %s", self._key)
                # Request immediate refresh to update the state
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("[SWITCH] Failed to turn off %s", self._key)
                
        except Exception as e:
            _LOGGER.error("[SWITCH] Error turning off switch %s: %s", self._key, e)
            import traceback
            _LOGGER.error("[SWITCH] Traceback: %s", traceback.format_exc())
