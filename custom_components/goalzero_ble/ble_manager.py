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
    ALTA80_WRITE_HANDLE,
    ALTA80_READ_HANDLE,
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

    async def send_command_with_handles(
        self, 
        command_hex: str, 
        write_handle: int, 
        read_handle: int,
        expected_responses: int = 2,
        timeout: int = 10
    ) -> list[str]:
        """Send a command using specific GATT handles and collect responses."""
        if not self._connected or not self.client:
            if not await self.connect():
                return []

        responses = []
        response_count = 0

        def handle_notification(sender, data):
            nonlocal response_count, responses
            response_count += 1
            hex_data = data.hex().upper()
            _LOGGER.debug("Handle response %d: %s", response_count, hex_data)
            responses.append(hex_data)

        try:
            # Find characteristics by handle
            write_char = None
            read_char = None
            
            services = self.client.services
            for service in services.services.values():
                for char in service.characteristics:
                    if char.handle == write_handle:
                        write_char = char
                    if char.handle == read_handle:
                        read_char = char
            
            if not write_char or not read_char:
                _LOGGER.error(
                    "Required handles not found. Write: 0x%04X (%s), Read: 0x%04X (%s)",
                    write_handle, write_char is not None,
                    read_handle, read_char is not None
                )
                return []
            
            # Start notifications
            await self.client.start_notify(read_char, handle_notification)
            
            # Send command
            command_bytes = bytes.fromhex(command_hex)
            await self.client.write_gatt_char(write_char, command_bytes)
            _LOGGER.debug("Sent command to handle 0x%04X: %s", write_handle, command_hex)
            
            # Wait for expected responses
            elapsed = 0
            while response_count < expected_responses and elapsed < timeout:
                await asyncio.sleep(0.1)
                elapsed += 0.1
            
            # Stop notifications
            await self.client.stop_notify(read_char)
            
            return responses
            
        except Exception as e:
            _LOGGER.error("Failed to send command with handles: %s", e)
            return []

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
