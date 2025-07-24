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
            _LOGGER.warning("Cannot connect: device %s not discoverable", self.address)
            return False

        try:
            # Clean up any existing connection
            if self._client:
                try:
                    if self._client.is_connected:
                        await asyncio.wait_for(
                            self._client.disconnect(), timeout=BLE_DISCONNECT_TIMEOUT
                        )
                except Exception as e:
                    _LOGGER.debug("Error cleaning up old connection: %s", e)
                finally:
                    self._client = None

            if not self._device:
                _LOGGER.error("Device object is None, cannot connect")
                return False
                
            _LOGGER.debug("Attempting to connect to %s (%s)", self._device.name, self.address)
            self._client = BleakClient(self._device)
            
            # Use asyncio.wait_for with proper timeout handling
            await asyncio.wait_for(
                self._client.connect(), timeout=BLE_CONNECT_TIMEOUT
            )
            
            if not self._client.is_connected:
                _LOGGER.error("Connection established but client reports not connected")
                self._client = None
                return False
            
            self._connected = True
            _LOGGER.info("Successfully connected to device %s (%s)", self._device.name, self.address)
            return True
            
        except asyncio.TimeoutError:
            _LOGGER.error("Connection timeout after %ds for device %s", BLE_CONNECT_TIMEOUT, self.address)
            self._connected = False
            self._client = None
            return False
        except Exception as e:
            _LOGGER.error("Failed to connect to %s: %s (type: %s)", self.address, e, type(e).__name__)
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
            available_handles = []
            
            for service in services.services.values():
                for char in service.characteristics:
                    available_handles.append(f"0x{char.handle:04X}")
                    if char.handle == write_handle:
                        write_char = char
                    if char.handle == read_handle:
                        read_char = char

            if not write_char or not read_char:
                _LOGGER.error(
                    "Required characteristics not found for %s. "
                    "Write: 0x%04X (%s), Read: 0x%04X (%s). "
                    "Available handles: %s",
                    self.address, write_handle, write_char is not None, 
                    read_handle, read_char is not None,
                    ", ".join(available_handles)
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

    async def discover_gatt_services(self) -> dict:
        """Discover and log all GATT services and characteristics for debugging."""
        if not self._connected or not self._client:
            _LOGGER.error("Not connected to device %s for GATT discovery", self.address)
            return {}

        try:
            services_info = {}
            services = self._client.services
            
            _LOGGER.info("=== GATT Discovery for %s ===", self.address)
            for service in services.services.values():
                service_info = {
                    "uuid": str(service.uuid),
                    "characteristics": []
                }
                
                _LOGGER.info("Service: %s", service.uuid)
                for char in service.characteristics:
                    char_info = {
                        "uuid": str(char.uuid),
                        "handle": f"0x{char.handle:04X}",
                        "properties": [prop for prop in char.properties]
                    }
                    service_info["characteristics"].append(char_info)
                    
                    _LOGGER.info(
                        "  Characteristic: %s (Handle: 0x%04X, Properties: %s)", 
                        char.uuid, char.handle, char.properties
                    )
                    
                    for descriptor in char.descriptors:
                        _LOGGER.info(
                            "    Descriptor: %s (Handle: 0x%04X)", 
                            descriptor.uuid, descriptor.handle
                        )
                
                services_info[str(service.uuid)] = service_info
            
            _LOGGER.info("=== End GATT Discovery ===")
            return services_info
            
        except Exception as e:
            _LOGGER.error("Error during GATT discovery for %s: %s", self.address, e)
            return {}

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
