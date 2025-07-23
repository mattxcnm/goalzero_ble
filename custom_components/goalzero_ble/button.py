"""Button platform for Goal Zero BLE integration."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    ALTA_80,
    BATTERY_PROTECTION_COMMANDS,
    ECO_COMMANDS,
)
from .coordinator import GoalZeroCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Goal Zero BLE buttons."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        # Temperature control buttons
        GoalZeroTempButton(coordinator, config_entry, "left_setpoint_up", "Left Zone Temp Up", "mdi:thermometer-plus"),
        GoalZeroTempButton(coordinator, config_entry, "left_setpoint_down", "Left Zone Temp Down", "mdi:thermometer-minus"),
        GoalZeroTempButton(coordinator, config_entry, "right_setpoint_up", "Right Zone Temp Up", "mdi:thermometer-plus"),
        GoalZeroTempButton(coordinator, config_entry, "right_setpoint_down", "Right Zone Temp Down", "mdi:thermometer-minus"),
        
        # Eco mode buttons
        GoalZeroModeButton(coordinator, config_entry, "eco_on", "Eco Mode On", "mdi:leaf", ECO_COMMANDS),
        GoalZeroModeButton(coordinator, config_entry, "eco_off", "Eco Mode Off", "mdi:leaf-off", ECO_COMMANDS),
        
        # Battery protection buttons
        GoalZeroModeButton(coordinator, config_entry, "high", "Battery Protection High", "mdi:battery-high", BATTERY_PROTECTION_COMMANDS),
        GoalZeroModeButton(coordinator, config_entry, "med", "Battery Protection Medium", "mdi:battery-medium", BATTERY_PROTECTION_COMMANDS),
        GoalZeroModeButton(coordinator, config_entry, "low", "Battery Protection Low", "mdi:battery-low", BATTERY_PROTECTION_COMMANDS),
    ]
    
    async_add_entities(entities)


class GoalZeroBaseButton(CoordinatorEntity, ButtonEntity):
    """Base button for Goal Zero devices."""

    def __init__(self, coordinator: GoalZeroCoordinator, config_entry: ConfigEntry, button_id: str, name: str, icon: str):
        """Initialize the button."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_unique_id = f"{coordinator.mac_address}_{button_id}"
        self._attr_name = f"{ALTA_80} {name}"
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.mac_address)},
            "name": f"{ALTA_80} ({coordinator.mac_address})",
            "manufacturer": MANUFACTURER,
            "model": ALTA_80,
        }


class GoalZeroTempButton(GoalZeroBaseButton):
    """Temperature control button."""

    def __init__(self, coordinator: GoalZeroCoordinator, config_entry: ConfigEntry, command_key: str, name: str, icon: str):
        """Initialize the temperature button."""
        super().__init__(coordinator, config_entry, command_key, name, icon)
        self.command_key = command_key

    async def async_press(self) -> None:
        """Handle button press."""
        await self.coordinator.send_command(self.command_key)


class GoalZeroModeButton(GoalZeroBaseButton):
    """Mode control button."""

    def __init__(self, coordinator: GoalZeroCoordinator, config_entry: ConfigEntry, command_key: str, name: str, icon: str, command_dict: dict):
        """Initialize the mode button."""
        super().__init__(coordinator, config_entry, command_key, name, icon)
        self.command_key = command_key
        self.command_dict = command_dict

    async def async_press(self) -> None:
        """Handle button press."""
        if self.command_key in self.command_dict:
            await self.coordinator.send_custom_command(self.command_dict[self.command_key])
