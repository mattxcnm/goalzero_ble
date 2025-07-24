"""BLE Manager for Goal Zero devices."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from .const import (
    BLE_CONNECT_TIMEOUT,
    BLE_DISCONNECT_TIMEOUT,
    BLE_SCAN_TIMEOUT,
    BLE_COMMAND_TIMEOUT,
)
from .device_registry import DeviceRegistry

_LOGGER = logging.getLogger(__name__)


class GoalZeroBLEManager:
    """Manages BLE communication with Goal Zero devices."""

    def __init__(self, address: str, device_type: str) -> None:
        """Initialize the BLE manager."""
        self.address = address.upper()
        self.device_type = device_type
        self.device_handles = DeviceRegistry.get_device_handles(device_type)
        
        self._client: Optional[BleakClient] = None
        self._device: Optional[BLEDevice] = None
        self._connected = False
        self._connection_lock = asyncio.Lock()
        
        _LOGGER.debug(
            "Initialized BLE manager for %s (%s) with handles: %s",
            self.address, self.device_type, self.device_handles
        )

    async def discover_device(self) -> bool:
        """Discover the device by MAC address."""
        try:
            _LOGGER.debug("Scanning for device %s", self.address)
            device = await BleakScanner.find_device_by_address(
                self.address, timeout=BLE_SCAN_TIMEOUT
            )
            if device:
                self._device = device
                _LOGGER.info("Found device: %s (%s)", device.name, self.address)
                return True
            else:
                _LOGGER.warning("Device %s not found during scan", self.address)
                return False
        except Exception as e:
            _LOGGER.error("Error discovering device %s: %s", self.address, e)
            return False

    async def ensure_connected(self) -> bool:
        """Ensure connection to the device, connecting if necessary."""
        async with self._connection_lock:
            if self._connected and self._client and self._client.is_connected:
                return True
            
            return await self._connect_internal()

    async def _connect_internal(self) -> bool:
        """Internal connection method (must be called with lock held)."""
        if not self._device and not await self.discover_device():
            return False

        try:
            if self._client:
                try:
                    await self._client.disconnect()
                except Exception:
                    pass  # Ignore disconnect errors
                self._client = None

            if not self._device:
                return False
                
            self._client = BleakClient(self._device)
            await asyncio.wait_for(
                self._client.connect(), timeout=BLE_CONNECT_TIMEOUT
            )
            
            self._connected = True
            _LOGGER.info("Connected to device %s", self.address)
            return True
            
        except Exception as e:
            _LOGGER.error("Failed to connect to %s: %s", self.address, e)
            self._connected = False
            self._client = None
            return False

    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        async with self._connection_lock:
            if self._client:
                try:
                    if self._client.is_connected:
                        await asyncio.wait_for(
                            self._client.disconnect(), timeout=BLE_DISCONNECT_TIMEOUT
                        )
                except Exception as e:
                    _LOGGER.error("Error disconnecting from %s: %s", self.address, e)
                finally:
                    self._client = None
                    self._connected = False
                    _LOGGER.info("Disconnected from device %s", self.address)

    async def send_command(self, command_hex: str) -> bool:
        """Send a command to the device using GATT handles."""
        if not self._connected or not self._client:
            _LOGGER.error("Not connected to device %s", self.address)
            return False

        try:
            write_handle = self.device_handles.get("write")
            if not write_handle:
                _LOGGER.error("No write handle defined for device type %s", self.device_type)
                return False

            # Find write characteristic by handle
            write_char = None
            services = self._client.services
            for service in services.services.values():
                for char in service.characteristics:
                    if char.handle == write_handle:
                        write_char = char
                        break
                if write_char:
                    break

            if not write_char:
                _LOGGER.error(
                    "Write characteristic not found at handle 0x%04X for %s",
                    write_handle, self.address
                )
                return False

            # Send command
            command_bytes = bytes.fromhex(command_hex)
            await self._client.write_gatt_char(write_char, command_bytes)
            _LOGGER.debug("Sent command to %s: %s", self.address, command_hex)
            return True
            
        except Exception as e:
            _LOGGER.error("Failed to send command to %s: %s", self.address, e)
            return False

    async def send_command_and_collect_responses(
        self, 
        command_hex: str,
        expected_responses: int = 2,
        timeout: int = BLE_COMMAND_TIMEOUT
    ) -> list[str]:
        """Send a command and collect responses using GATT handles."""
        if not self._connected or not self._client:
            _LOGGER.error("Not connected to device %s", self.address)
            return []

        write_handle = self.device_handles.get("write")
        read_handle = self.device_handles.get("read")
        
        if not write_handle or not read_handle:
            _LOGGER.error(
                "Missing GATT handles for device type %s (write: %s, read: %s)",
                self.device_type, write_handle, read_handle
            )
            return []

        responses = []
        response_count = 0

        def handle_notification(sender, data):
            nonlocal response_count, responses
            response_count += 1
            hex_data = data.hex().upper()
            _LOGGER.debug("Response %d from %s: %s", response_count, self.address, hex_data)
            responses.append(hex_data)

        try:
            # Find characteristics by handle
            write_char = None
            read_char = None
            
            services = self._client.services
            for service in services.services.values():
                for char in service.characteristics:
                    if char.handle == write_handle:
                        write_char = char
                    if char.handle == read_handle:
                        read_char = char

            if not write_char or not read_char:
                _LOGGER.error(
                    "Required characteristics not found for %s. Write: 0x%04X (%s), Read: 0x%04X (%s)",
                    self.address, write_handle, write_char is not None, 
                    read_handle, read_char is not None
                )
                return []

            # Start notifications
            await self._client.start_notify(read_char, handle_notification)

            # Send command
            command_bytes = bytes.fromhex(command_hex)
            await self._client.write_gatt_char(write_char, command_bytes)
            _LOGGER.debug("Sent command to %s: %s", self.address, command_hex)

            # Wait for expected responses
            elapsed = 0
            while response_count < expected_responses and elapsed < timeout:
                await asyncio.sleep(0.1)
                elapsed += 0.1

            # Stop notifications
            await self._client.stop_notify(read_char)

            _LOGGER.debug(
                "Collected %d responses from %s (expected %d)",
                len(responses), self.address, expected_responses
            )
            return responses

        except Exception as e:
            _LOGGER.error("Failed to send command and collect responses from %s: %s", self.address, e)
            return []

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return (
            self._connected and 
            self._client is not None and 
            self._client.is_connected
        )

    @property
    def device_address(self) -> str:
        """Return the device address."""
        return self.address

    @property
    def client(self) -> BleakClient | None:
        """Return the BLE client for direct access if needed."""
        return self._client if self._connected else None
