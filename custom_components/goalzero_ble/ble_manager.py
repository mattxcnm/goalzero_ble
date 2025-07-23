"""BLE Manager for Goal Zero devices."""
import asyncio
import logging
from typing import Callable, Optional

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from .const import (
    BLE_CONNECT_TIMEOUT,
    BLE_DISCONNECT_TIMEOUT,
    BLE_SCAN_TIMEOUT,
    NOTIFY_CHAR_UUID,
    SERVICE_UUID,
    WRITE_CHAR_UUID,
)

_LOGGER = logging.getLogger(__name__)


class GoalZeroBLEManager:
    """Manages BLE communication with Goal Zero devices."""

    def __init__(self, mac_address: str, data_callback: Optional[Callable] = None):
        """Initialize the BLE manager."""
        self.mac_address = mac_address.upper()
        self.data_callback = data_callback
        self.client: Optional[BleakClient] = None
        self.device: Optional[BLEDevice] = None
        self._connected = False
        self._connection_lock = asyncio.Lock()

    async def discover_device(self) -> bool:
        """Discover the device by MAC address."""
        try:
            _LOGGER.debug("Scanning for device %s", self.mac_address)
            device = await BleakScanner.find_device_by_address(
                self.mac_address, timeout=BLE_SCAN_TIMEOUT
            )
            if device:
                self.device = device
                _LOGGER.info("Found device: %s", device.name)
                return True
            else:
                _LOGGER.warning("Device %s not found", self.mac_address)
                return False
        except Exception as e:
            _LOGGER.error("Error discovering device: %s", e)
            return False

    async def connect(self) -> bool:
        """Connect to the BLE device."""
        async with self._connection_lock:
            if self._connected:
                return True

            if not self.device and not await self.discover_device():
                return False

            try:
                self.client = BleakClient(self.device)
                await asyncio.wait_for(
                    self.client.connect(), timeout=BLE_CONNECT_TIMEOUT
                )
                
                # Start notifications if callback is provided
                if self.data_callback:
                    await self.client.start_notify(
                        NOTIFY_CHAR_UUID, self._notification_handler
                    )
                
                self._connected = True
                _LOGGER.info("Connected to device %s", self.mac_address)
                return True
                
            except Exception as e:
                _LOGGER.error("Failed to connect: %s", e)
                self._connected = False
                return False

    async def disconnect(self):
        """Disconnect from the BLE device."""
        async with self._connection_lock:
            if self.client and self._connected:
                try:
                    await asyncio.wait_for(
                        self.client.disconnect(), timeout=BLE_DISCONNECT_TIMEOUT
                    )
                except Exception as e:
                    _LOGGER.error("Error disconnecting: %s", e)
                finally:
                    self._connected = False
                    _LOGGER.info("Disconnected from device %s", self.mac_address)

    async def send_command(self, command_hex: str) -> bool:
        """Send a command to the device."""
        if not self._connected or not self.client:
            if not await self.connect():
                return False

        try:
            command_bytes = bytes.fromhex(command_hex)
            await self.client.write_gatt_char(WRITE_CHAR_UUID, command_bytes)
            _LOGGER.debug("Sent command: %s", command_hex)
            return True
        except Exception as e:
            _LOGGER.error("Failed to send command %s: %s", command_hex, e)
            return False

    def _notification_handler(self, sender, data: bytearray):
        """Handle notifications from the device."""
        hex_data = data.hex().upper()
        _LOGGER.debug("Received notification: %s", hex_data)
        if self.data_callback:
            self.data_callback(hex_data)

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._connected
