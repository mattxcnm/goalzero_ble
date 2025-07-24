"""Goal Zero Alta 80 device implementation."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature

from .base import GoalZeroDevice
from ..const import DEVICE_TYPE_ALTA80, ALTA_80_MODEL

_LOGGER = logging.getLogger(__name__)


class Alta80Device(GoalZeroDevice):
    """Goal Zero Alta 80 fridge system device."""

    @property
    def device_type(self) -> str:
        """Return the device type identifier."""
        return DEVICE_TYPE_ALTA80

    @property
    def model(self) -> str:
        """Return the device model name."""
        return ALTA_80_MODEL

    def get_sensors(self) -> list[dict[str, Any]]:
        """Return list of sensor definitions for this device."""
        sensors = []
        
        # Raw status bytes (0-35, exactly 36 bytes total)
        for i in range(36):  # Exactly 36 bytes in concatenated response
            sensors.append({
                "key": f"status_byte_{i}",
                "name": f"Status Byte {i}",
                "device_class": None,
                "state_class": None,
                "unit": None,
                "icon": "mdi:hexadecimal",
            })
        
        # Decoded sensors for known bytes
        sensors.extend([
            {
                "key": "zone_1_temp",
                "name": "Zone 1 Temperature",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfTemperature.CELSIUS,
                "icon": "mdi:thermometer",
            },
            {
                "key": "zone_1_setpoint_exceeded",
                "name": "Zone 1 Setpoint Exceeded",
                "device_class": None,
                "state_class": None,
                "unit": None,
                "icon": "mdi:alert-circle",
            },
            {
                "key": "zone_2_temp_high_res",
                "name": "Zone 2 Temperature (High Res)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": UnitOfTemperature.CELSIUS,
                "icon": "mdi:thermometer",
            },
            {
                "key": "compressor_state_a",
                "name": "Compressor State A",
                "device_class": None,
                "state_class": None,
                "unit": None,
                "icon": "mdi:hvac",
            },
            {
                "key": "compressor_state_b",
                "name": "Compressor State B",
                "device_class": None,
                "state_class": None,
                "unit": None,
                "icon": "mdi:hvac",
            },
            {
                "key": "concatenated_response",
                "name": "Full Status Response",
                "device_class": None,
                "state_class": None,
                "unit": None,
                "icon": "mdi:code-string",
            },
            {
                "key": "response_length",
                "name": "Response Length",
                "device_class": None,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": "bytes",
                "icon": "mdi:counter",
            },
        ])
        
        return sensors

    def get_buttons(self) -> list[dict[str, Any]]:
        """Return list of button definitions for this device."""
        return [
            {
                "key": "temp_up",
                "name": "Temperature Up",
                "icon": "mdi:thermometer-plus",
            },
            {
                "key": "temp_down",
                "name": "Temperature Down",
                "icon": "mdi:thermometer-minus",
            },
            {
                "key": "power_on",
                "name": "Power On",
                "icon": "mdi:power",
            },
            {
                "key": "power_off",
                "name": "Power Off",
                "icon": "mdi:power-off",
            },
            {
                "key": "eco_on",
                "name": "Eco Mode On",
                "icon": "mdi:leaf",
            },
            {
                "key": "eco_off",
                "name": "Eco Mode Off",
                "icon": "mdi:leaf-off",
            },
        ]

    async def update_data(self, ble_manager) -> dict[str, Any]:
        """Update device data from BLE connection with improved reliability."""
        try:
            _LOGGER.debug("Updating Alta 80 data via direct BLE connection")
            
            # Import here to avoid circular imports
            from bleak import BleakClient, BleakScanner
            import bleak.exc
            
            # Find device by name with longer scan time for reliability
            device_address = None
            _LOGGER.debug("Scanning for device: %s", self.name)
            
            # Try scanning twice if first attempt fails
            for scan_attempt in range(2):
                try:
                    _LOGGER.debug("Scan attempt %d for device %s", scan_attempt + 1, self.name)
                    
                    # Use longer timeout for device discovery
                    devices = await BleakScanner.discover(timeout=20.0)
                    
                    found_devices = []
                    for device in devices:
                        if device.name:
                            found_devices.append(f"{device.name} ({device.address})")
                            if device.name == self.name:
                                device_address = device.address
                                _LOGGER.info("✓ Found target device: %s (%s) on attempt %d", 
                                           device.name, device.address, scan_attempt + 1)
                                break
                    
                    if device_address:
                        break
                        
                    if scan_attempt == 0:
                        _LOGGER.warning("Device %s not found on first scan. Found devices: %s", 
                                      self.name, ", ".join(found_devices[:5]))  # Show first 5
                        _LOGGER.info("Retrying scan in 3 seconds...")
                        await asyncio.sleep(3)  # Longer pause before retry
                        
                except Exception as e:
                    _LOGGER.warning("Scan attempt %d failed: %s", scan_attempt + 1, e)
                    if scan_attempt == 0:
                        await asyncio.sleep(3)
            
            if not device_address:
                _LOGGER.error("Device %s not found after scanning attempts", self.name)
                return self._get_default_data()
            
            # Attempt connection with retry logic
            return await self._connect_and_read_data(device_address)
            
        except Exception as e:
            _LOGGER.error("Error updating Alta 80 data: %s (type: %s)", e, type(e).__name__)
            self._data = self._get_default_data()
            return self._data

    async def _connect_and_read_data(self, device_address: str, max_retries: int = 2) -> dict[str, Any]:
        """Connect to device and read data with retry logic."""
        from bleak import BleakClient
        import bleak.exc
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                _LOGGER.info("Connection attempt %d/%d to %s (%s)", 
                           attempt + 1, max_retries, self.name, device_address)
                
                # Use connection timeout and add disconnected_callback
                async with BleakClient(
                    device_address, 
                    timeout=15.0,
                    disconnected_callback=self._on_disconnect
                ) as client:
                    _LOGGER.info("✓ Connected to Alta 80 device %s (%s)", self.name, device_address)
                    
                    # Brief delay to ensure connection is stable and device is ready
                    await asyncio.sleep(1.0)  # Increased from 0.5 to 1.0 seconds
                    
                    # Perform data read
                    return await self._read_device_data(client)
                    
            except asyncio.TimeoutError as e:
                last_error = e
                _LOGGER.warning("Connection timeout on attempt %d/%d: %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)  # Wait before retry
                    
            except bleak.exc.BleakError as e:
                last_error = e
                error_msg = str(e)
                if "ESP_GATT_CONN_FAIL_ESTABLISH" in error_msg:
                    _LOGGER.warning("BLE connection failed to establish on attempt %d/%d: %s", 
                                  attempt + 1, max_retries, e)
                    # Longer wait for connection establishment failures
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                else:
                    _LOGGER.warning("BLE error on attempt %d/%d: %s", attempt + 1, max_retries, e)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(3)
                        
            except Exception as e:
                last_error = e
                _LOGGER.warning("Unexpected error on attempt %d/%d: %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
        
        # All attempts failed
        _LOGGER.error("All connection attempts failed. Last error: %s", last_error)
        return self._get_default_data()

    def _on_disconnect(self, client):
        """Callback for when device disconnects."""
        _LOGGER.debug("Device %s disconnected", self.name)

    async def _read_device_data(self, client) -> dict[str, Any]:
        """Read data from connected device."""
        responses = []
        response_count = 0
        
        def notification_handler(sender, data):
            nonlocal response_count, responses
            response_count += 1
            hex_data = data.hex().upper()
            _LOGGER.debug("Alta 80 Response %d: %s", response_count, hex_data)
        try:
            # Find characteristics dynamically by properties instead of hardcoded handles
            write_char = None
            read_char = None
            
            services = client.services
            available_handles = []
            
            _LOGGER.info("=== Alta 80 GATT Discovery ===")
            for service in services.services.values():
                _LOGGER.info("Service: %s", service.uuid)
                for char in service.characteristics:
                    available_handles.append(f"0x{char.handle:04X}")
                    properties = char.properties
                    _LOGGER.info(
                        "  Characteristic: %s (Handle: 0x%04X, Properties: %s)", 
                        char.uuid, char.handle, properties
                    )
                    
                    # Look for write characteristic (typically has 'write' or 'write-without-response')
                    if not write_char and ('write' in properties or 'write-without-response' in properties):
                        write_char = char
                        _LOGGER.info("✓ Selected write characteristic: 0x%04X", char.handle)
                    
                    # Look for read/notify characteristic (typically has 'notify' or 'read')
                    if not read_char and ('notify' in properties or 'indicate' in properties):
                        read_char = char
                        _LOGGER.info("✓ Selected read/notify characteristic: 0x%04X", char.handle)
            
            _LOGGER.info("=== End GATT Discovery ===")
            
            if not write_char or not read_char:
                _LOGGER.error(
                    "Required characteristics not found for Alta 80. "
                    "Write char: %s (handle: %s), Read/notify char: %s (handle: %s). "
                    "Available handles: %s",
                    write_char is not None, 
                    f"0x{write_char.handle:04X}" if write_char else "None",
                    read_char is not None,
                    f"0x{read_char.handle:04X}" if read_char else "None",
                    ", ".join(available_handles)
                )
                return self._get_default_data()
            
            # Start notifications
            await client.start_notify(read_char, notification_handler)
            
            # Wait a moment for notifications to be set up
            await asyncio.sleep(0.5)
            
            # Send status request command - try twice if no response
            command_bytes = bytes.fromhex("FEFE03010200")
            
            for command_attempt in range(2):
                _LOGGER.debug("Sending status command attempt %d: FEFE03010200", command_attempt + 1)
                await client.write_gatt_char(write_char, command_bytes)
                
                # Wait for initial response
                initial_wait = 3  # Wait 3 seconds for first response
                elapsed = 0
                initial_response_count = response_count
                
                while response_count == initial_response_count and elapsed < initial_wait:
                    await asyncio.sleep(0.1)
                    elapsed += 0.1
                
                if response_count > initial_response_count:
                    _LOGGER.debug("Got response on command attempt %d", command_attempt + 1)
                    break
                elif command_attempt == 0:
                    _LOGGER.warning("No response to first command, retrying...")
                    await asyncio.sleep(1)  # Wait before retry
            
            # Wait for all expected responses (expecting 2 responses total)
            timeout_duration = 12  # Increased timeout
            elapsed = 0
            while response_count < 2 and elapsed < timeout_duration:
                await asyncio.sleep(0.1)
                elapsed += 0.1
            
            if response_count == 0:
                _LOGGER.warning("No responses received from Alta 80 within %ds", timeout_duration)
            elif response_count < 2:
                _LOGGER.warning("Only received %d of 2 expected responses from Alta 80", response_count)
            else:
                _LOGGER.debug("Received all %d expected responses from Alta 80", response_count)
            
            # Stop notifications
            try:
                await client.stop_notify(read_char)
            except Exception as e:
                _LOGGER.debug("Error stopping notifications: %s", e)
            
            # Parse responses if we got them
            if responses:
                parsed_data = self._parse_status_responses(responses)
                _LOGGER.debug("Successfully parsed Alta 80 data with %d sensor values", len(parsed_data))
                return parsed_data
            else:
                _LOGGER.warning("No responses received from Alta 80 device")
                return self._get_default_data()
                
        except Exception as e:
            _LOGGER.error("Error reading device data: %s", e)
            return self._get_default_data()

    def _get_default_data(self) -> dict[str, Any]:
        """Return default data structure with None values."""
        data = {}
        
        # Initialize all status bytes to None (exactly 36 bytes)
        for i in range(36):
            data[f"status_byte_{i}"] = None
        
        # Initialize decoded values
        data.update({
            "zone_1_temp": None,
            "zone_1_setpoint_exceeded": None,
            "zone_2_temp_high_res": None,
            "compressor_state_a": None,
            "compressor_state_b": None,
            "concatenated_response": None,
            "response_length": None,
        })
        
        return data

    def _parse_status_responses(self, responses: list[str]) -> dict[str, Any]:
        """Parse GATT responses from Alta 80 device into individual bytes."""
        parsed_data = self._get_default_data()
        
        try:
            # Concatenate all responses
            concatenated_response = "".join(responses)
            parsed_data["concatenated_response"] = concatenated_response
            
            # Convert to bytes
            all_bytes = bytes.fromhex(concatenated_response)
            parsed_data["response_length"] = len(all_bytes)
            
            _LOGGER.debug("Parsing %d total bytes from concatenated response", len(all_bytes))
            
            # Parse each byte individually (exactly 36 bytes)
            for i, byte_val in enumerate(all_bytes):
                if i < 36:  # Exactly 36 bytes in response
                    parsed_data[f"status_byte_{i}"] = byte_val
            
            # Validate expected response length
            if len(all_bytes) != 36:
                _LOGGER.warning("Expected 36 bytes, got %d bytes in response", len(all_bytes))
            
            # Parse known decoded bytes
            if len(all_bytes) > 18:
                # Byte 18: Zone 1 temp (signed integer)
                zone_1_temp_raw = all_bytes[18]
                if zone_1_temp_raw > 127:  # Convert to signed
                    zone_1_temp_raw = zone_1_temp_raw - 256
                parsed_data["zone_1_temp"] = zone_1_temp_raw
                _LOGGER.debug("Zone 1 temp (byte 18): %d°C", zone_1_temp_raw)
            
            if len(all_bytes) > 34:
                # Byte 34: Zone 1 setpoint exceeded (boolean-ish)
                setpoint_exceeded = all_bytes[34]
                parsed_data["zone_1_setpoint_exceeded"] = bool(setpoint_exceeded)
                _LOGGER.debug("Zone 1 setpoint exceeded (byte 34): %s", setpoint_exceeded)
            
            if len(all_bytes) > 35:
                # Byte 35: Zone 2 temp high resolution
                zone_2_temp_high_res = all_bytes[35]
                # This might be a high resolution value, possibly needs scaling
                parsed_data["zone_2_temp_high_res"] = zone_2_temp_high_res / 10.0 if zone_2_temp_high_res != 0 else 0
                _LOGGER.debug("Zone 2 temp high res (byte 35): %.1f", parsed_data["zone_2_temp_high_res"])
            
            # Note: You mentioned "compressor state a" and "compressor state b" but didn't specify
            # which bytes they are. I'll add placeholders that can be updated when the byte positions are known
            # Since we only have 36 bytes (0-35), these would need to be within that range
            if len(all_bytes) >= 36:  # Check we have all 36 bytes
                # Placeholder positions - update with actual byte positions when known
                # These are just examples using the last few bytes
                if len(all_bytes) > 34:  # Use byte 34 for compressor_state_a
                    parsed_data["compressor_state_a"] = all_bytes[34]
                    _LOGGER.debug("Compressor state A (byte 34): %d", all_bytes[34])
                
                if len(all_bytes) > 35:  # Use byte 35 for compressor_state_b
                    parsed_data["compressor_state_b"] = all_bytes[35]
                    _LOGGER.debug("Compressor state B (byte 35): %d", all_bytes[35])
            
            _LOGGER.debug("Successfully parsed Alta 80 status data")
            
        except Exception as e:
            _LOGGER.error("Error parsing Alta 80 status responses: %s", e)
        
        return parsed_data

    def parse_ble_data(self, data: bytes) -> dict[str, Any]:
        """Parse BLE data specific to Alta 80 fridge system."""
        # Convert single data packet to hex string format for consistency
        hex_data = data.hex().upper()
        return self._parse_status_responses([hex_data])
