"""Base entity for Goal Zero BLE devices."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import GoalZeroCoordinator


class GoalZeroEntity(CoordinatorEntity[GoalZeroCoordinator]):
    """Base class for Goal Zero entities."""

    def __init__(
        self,
        coordinator: GoalZeroCoordinator,
        key: str,
        name: str,
        icon: str | None = None,
    ) -> None:
        """Initialize the Goal Zero entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"{coordinator.device_name} {name}"
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.device.address}_{key}"
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Goal Zero device."""
        device = self.coordinator.device
        return DeviceInfo(
            identifiers={(DOMAIN, device.address)},
            name=device.name,
            manufacturer=MANUFACTURER,
            model=device.model,
            # Don't set via_device to avoid self-reference since this IS the device
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
