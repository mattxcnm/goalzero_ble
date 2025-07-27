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

_LOGGER = logging.getLogger(__name__)


class GoalZeroBLEManager:
    """Manages BLE communication with Goal Zero devices."""

    def __init__(self, address: str, device_type: str) -> None:
        """Initialize the BLE manager."""
        self.address = address.upper()
        self.device_type = device_type
        
        self._client: Optional[BleakClient] = None
        self._device: Optional[BLEDevice] = None
        self._connected = False
        self._connection_lock = asyncio.Lock()
        
        _LOGGER.debug(
            "Initialized BLE manager for %s (%s) with dynamic GATT discovery",
            self.address, self.device_type
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

    async def send_command(self, command_data: str | bytes) -> bool:
        """Send a command to the device using dynamic GATT discovery.
        
        Args:
            command_data: Command as hex string or bytes
            
        Returns:
            True if command was sent successfully
        """
        _LOGGER.info("[BLEManager] send_command: Connected=%s, Client=%s", self._connected, self._client is not None)
        _LOGGER.info("[BLEManager] Command data type: %s", type(command_data).__name__)
        if not self._connected or not self._client:
            _LOGGER.error("[BLEManager] Not connected to device %s (connected: %s, client: %s)", self.address, self._connected, self._client is not None)
            return False
        try:
            if isinstance(command_data, str):
                command_bytes = bytes.fromhex(command_data)
                command_hex = command_data
            else:
                command_bytes = command_data
                command_hex = command_data.hex().upper()
            _LOGGER.info("[BLEManager] Command to send: %s (%d bytes)", command_hex, len(command_bytes))
            write_char = await self._find_write_characteristic()
            if not write_char:
                _LOGGER.error("[BLEManager] No write characteristic found for device %s", self.address)
                if self._client:
                    _LOGGER.error("[BLEManager] Available characteristics:")
                    services = self._client.services
                    for service in services.services.values():
                        _LOGGER.error("  Service: %s", service.uuid)
                        for char in service.characteristics:
                            _LOGGER.error("    Char: %s (Handle: 0x%04X, Properties: %s)", char.uuid, char.handle, char.properties)
                return False
            _LOGGER.info("[BLEManager] Using write characteristic: %s (Handle: 0x%04X, Properties: %s)", write_char.uuid, write_char.handle, write_char.properties)
            if 'write-without-response' in write_char.properties:
                _LOGGER.info("[BLEManager] Using write-without-response")
                await self._client.write_gatt_char(write_char, command_bytes, response=False)
            elif 'write' in write_char.properties:
                _LOGGER.info("[BLEManager] Using write-with-response")
                await self._client.write_gatt_char(write_char, command_bytes, response=True)
            else:
                _LOGGER.error("[BLEManager] Characteristic doesn't support writing")
                return False
            _LOGGER.info("[BLEManager] Command sent successfully to %s: %s", self.address, command_hex)
            return True
        except Exception as e:
            _LOGGER.error("[BLEManager] Failed to send command to %s: %s", self.address, e)
            import traceback
            _LOGGER.error("[BLEManager] Traceback: %s", traceback.format_exc())
            return False

    async def _find_write_characteristic(self):
        """Find a characteristic suitable for writing commands, with debug logging."""
        if not self._client:
            _LOGGER.error("_find_write_characteristic: No BLE client available!")
            return None

        services = self._client.services
        found_chars = []
        for service in services.services.values():
            _LOGGER.debug("Scanning service: %s", service.uuid)
            for char in service.characteristics:
                _LOGGER.debug("Characteristic: %s (Handle: 0x%04X, Properties: %s)", char.uuid, char.handle, char.properties)
                properties = char.properties
                if 'write' in properties or 'write-without-response' in properties:
                    _LOGGER.info("Found write characteristic: %s (Handle: 0x%04X, Properties: %s)", char.uuid, char.handle, properties)
                    found_chars.append(char)
        if not found_chars:
            _LOGGER.error("No write characteristic found! Available characteristics:")
            for service in services.services.values():
                for char in service.characteristics:
                    _LOGGER.error("  Char: %s (Handle: 0x%04X, Properties: %s)", char.uuid, char.handle, char.properties)
            return None
        # Prefer write-without-response if available
        for char in found_chars:
            if 'write-without-response' in char.properties:
                _LOGGER.info("Using write-without-response characteristic: %s (Handle: 0x%04X)", char.uuid, char.handle)
                return char
        # Otherwise, use first found
        _LOGGER.info("Using first found write characteristic: %s (Handle: 0x%04X)", found_chars[0].uuid, found_chars[0].handle)
        return found_chars[0]

    async def _find_notify_characteristic(self):
        """Find a characteristic suitable for notifications."""
        if not self._client:
            return None
            
        services = self._client.services
        for service in services.services.values():
            for char in service.characteristics:
                properties = char.properties
                if 'notify' in properties or 'indicate' in properties:
                    _LOGGER.debug("Found notify characteristic: 0x%04X with properties %s", char.handle, properties)
                    return char
        return None

    async def send_command_and_collect_responses(
        self, 
        command_hex: str,
        expected_responses: int = 2,
        timeout: int = BLE_COMMAND_TIMEOUT
    ) -> list[str]:
        """Send a command and collect responses using dynamic GATT discovery."""
        if not self._connected or not self._client:
            _LOGGER.error("Not connected to device %s", self.address)
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
            # Find characteristics dynamically
            write_char = await self._find_write_characteristic()
            read_char = await self._find_notify_characteristic()
            
            if not write_char or not read_char:
                _LOGGER.error(
                    "Required characteristics not found for %s. "
                    "Write char: %s, Notify char: %s",
                    self.address, write_char is not None, read_char is not None
                )
                
                # Log available characteristics for debugging
                await self.discover_gatt_services()
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

    async def send_command_to_device(self, device_name: str, command_data: str | bytes) -> bool:
        """Send a command to a specific device by name.
        
        Args:
            device_name: Name of the device to send command to
            command_data: Command as hex string or bytes
            
        Returns:
            True if command was sent successfully
        """
        _LOGGER.info("[BLEManager] send_command_to_device: Target device name: %s, Manager address: %s", device_name, self.address)
        try:
            if not self._connected:
                _LOGGER.warning("[BLEManager] Device not connected, attempting connection...")
                success = await self.ensure_connected()
                if not success:
                    _LOGGER.error("[BLEManager] Failed to connect to device %s for command", device_name)
                    return False
                _LOGGER.info("[BLEManager] Successfully connected for command send")
            else:
                _LOGGER.info("[BLEManager] Device already connected")
            result = await self.send_command(command_data)
            if result:
                _LOGGER.info("[BLEManager] Command sent to %s successfully!", device_name)
            else:
                _LOGGER.error("[BLEManager] Command send failed for %s!", device_name)
            return result
        except Exception as e:
            _LOGGER.error("[BLEManager] Exception sending command to device %s: %s", device_name, e)
            import traceback
            _LOGGER.error("[BLEManager] Traceback: %s", traceback.format_exc())
            return False

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
