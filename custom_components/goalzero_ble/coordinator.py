"""Data coordinator for Goal Zero BLE integration."""
import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble_manager import GoalZeroBLEManager
from .const import COMMANDS, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class GoalZeroCoordinator(DataUpdateCoordinator):
    """Data coordinator for Goal Zero devices."""

    def __init__(self, hass: HomeAssistant, mac_address: str):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.mac_address = mac_address
        self.ble_manager = GoalZeroBLEManager(
            mac_address, self._handle_notification
        )
        self._raw_data = ""
        self._pending_data = asyncio.Event()

    async def _async_update_data(self):
        """Fetch data from the device."""
        try:
            if not self.ble_manager.is_connected:
                if not await self.ble_manager.connect():
                    raise UpdateFailed("Failed to connect to device")

            # Send status request
            if await self.ble_manager.send_command(COMMANDS["status_request"]):
                # Wait for response with timeout
                try:
                    await asyncio.wait_for(self._pending_data.wait(), timeout=5.0)
                    self._pending_data.clear()
                    return {"raw_data": self._raw_data}
                except asyncio.TimeoutError:
                    raise UpdateFailed("Timeout waiting for device response")
            else:
                raise UpdateFailed("Failed to send status request")

        except Exception as e:
            _LOGGER.error("Error updating data: %s", e)
            raise UpdateFailed(f"Error updating data: {e}")

    def _handle_notification(self, data: str):
        """Handle incoming data from device."""
        self._raw_data = data
        self._pending_data.set()
        _LOGGER.debug("Received data: %s", data)

    async def send_command(self, command_key: str) -> bool:
        """Send a command to the device."""
        if command_key in COMMANDS:
            return await self.ble_manager.send_command(COMMANDS[command_key])
        return False

    async def send_custom_command(self, command_hex: str) -> bool:
        """Send a custom hex command to the device."""
        return await self.ble_manager.send_command(command_hex)

    async def async_shutdown(self):
        """Shutdown the coordinator."""
        await self.ble_manager.disconnect()
