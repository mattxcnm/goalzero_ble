"""Number platform for Goal Zero BLE devices."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
    """Set up Goal Zero number entities from a config entry."""
    coordinator: GoalZeroCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Get number definitions from device
    device = coordinator.device
    if hasattr(device, 'get_numbers'):
        number_definitions = device.get_numbers()
        
        for number_def in number_definitions:
            entities.append(
                GoalZeroNumberEntity(
                    coordinator,
                    number_def["key"],
                    number_def["name"],
                    number_def.get("icon"),
                    number_def.get("min_value", 0),
                    number_def.get("max_value", 100),
                    number_def.get("step", 1),
                    number_def.get("unit"),
                    number_def.get("mode", NumberMode.AUTO),
                )
            )
    
    if entities:
        async_add_entities(entities, update_before_add=True)


class GoalZeroNumberEntity(GoalZeroEntity, NumberEntity):
    """Goal Zero number entity."""

    def __init__(
        self,
        coordinator: GoalZeroCoordinator,
        key: str,
        name: str,
        icon: str | None,
        min_value: float,
        max_value: float,
        step: float,
        unit: str | None,
        mode: NumberMode,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, key, name, icon)
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_mode = mode

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        # Get current setpoint value from device data
        if self.coordinator.data:
            if self._key == "zone1_setpoint":
                return self.coordinator.data.get("zone_1_setpoint")
            elif self._key == "zone2_setpoint":
                return self.coordinator.data.get("zone_2_setpoint")
            else:
                return self.coordinator.data.get(self._key)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the number value."""
        _LOGGER.info("[NUMBER] User setting value '%.1f' for number '%s'", value, self._key)
        try:
            # Create command for the number entity
            device = self.coordinator.device
            _LOGGER.info("[NUMBER] Device type: %s", type(device).__name__)
            
            if hasattr(device, 'create_number_set_command'):
                _LOGGER.info("[NUMBER] Device has create_number_set_command method")
                command = device.create_number_set_command(self._key, value)
                _LOGGER.info("[NUMBER] Generated command: %s (%d bytes)", command.hex(':'), len(command))
                
                # Send command via BLE manager
                ble_manager = self.coordinator.ble_manager
                _LOGGER.info("[NUMBER] BLE manager type: %s", type(ble_manager).__name__)
                
                success = await device.send_command(ble_manager, command)
                
                if success:
                    _LOGGER.info("[NUMBER] Successfully set %s to %.1f", self._key, value)
                    await self.coordinator.async_request_refresh()
                else:
                    _LOGGER.error("[NUMBER] Failed to set %s to %.1f", self._key, value)
            else:
                _LOGGER.error("[NUMBER] Device does not support number commands")
                
        except Exception as e:
            _LOGGER.error("[NUMBER] Error setting number %s to %.1f: %s", self._key, value, e)
            import traceback
            _LOGGER.error("[NUMBER] Traceback: %s", traceback.format_exc())

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
