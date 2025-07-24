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
            device_obj = None
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
                                device_obj = device  # Store the device object, not just address
                                _LOGGER.info("✓ Found target device: %s (%s) on attempt %d", 
                                           device.name, device.address, scan_attempt + 1)
                                break
                    
                    if device_obj:
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
            
            if not device_obj:
                _LOGGER.error("Device %s not found after scanning attempts", self.name)
                return self._get_default_data()
            
            # Attempt connection with retry logic
            return await self._connect_and_read_data(device_obj)
            
        except Exception as e:
            _LOGGER.error("Error updating Alta 80 data: %s (type: %s)", e, type(e).__name__)
            self._data = self._get_default_data()
            return self._data

    async def _connect_and_read_data(self, device_obj, max_retries: int = 2) -> dict[str, Any]:
        """Connect to device and read data with retry logic."""
        from bleak import BleakClient
        import bleak.exc
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                _LOGGER.info("Connection attempt %d/%d to %s (%s)", 
                           attempt + 1, max_retries, device_obj.name, device_obj.address)
                
                # Use device object directly for connection
                async with BleakClient(
                    device_obj,  # Pass device object, not address string
                    timeout=15.0,
                    disconnected_callback=self._on_disconnect
                ) as client:
                    _LOGGER.info("✓ Connected to Alta 80 device %s (%s)", device_obj.name, device_obj.address)
                    
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
        _LOGGER.error("All connection attempts failed for %s (%s). Last error: %s", 
                     device_obj.name, device_obj.address, last_error)
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
            responses.append(hex_data)  # CRITICAL FIX: Actually store the response!
            _LOGGER.info("🔔 Alta 80 Notification %d from 0x%04X: %s (%d bytes)", 
                        response_count, sender.handle if hasattr(sender, 'handle') else 0, hex_data, len(data))
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
                    
                    # Look for write characteristic - prioritize write-without-response in custom service
                    if not write_char:
                        if 'write-without-response' in properties:
                            write_char = char
                            _LOGGER.info("✓ Selected write-without-response characteristic: 0x%04X", char.handle)
                        elif 'write' in properties and '1234' in str(service.uuid):  # Custom service
                            write_char = char
                            _LOGGER.info("✓ Selected write characteristic in custom service: 0x%04X", char.handle)
                    
                    # Look for read/notify characteristic (typically has 'notify' or 'read')
                    if not read_char and ('notify' in properties or 'indicate' in properties):
                        read_char = char
                        _LOGGER.info("✓ Selected read/notify characteristic: 0x%04X", char.handle)
            
            _LOGGER.info("=== End GATT Discovery ===")
            
            if not write_char or not read_char:
                _LOGGER.error(
                    "Required characteristics not found for Alta 80. "
                    "Write char: %s (handle: %s), Read/notify char: %s (handle: %s). "
                    "Available handles: %s. "
                    "Expected: write-without-response on service 00001234 (handle 0x000B) and notify on service 00001234 (handle 0x000D)",
                    write_char is not None, 
                    f"0x{write_char.handle:04X}" if write_char else "None",
                    read_char is not None,
                    f"0x{read_char.handle:04X}" if read_char else "None",
                    ", ".join(available_handles)
                )
                return self._get_default_data()
            
            _LOGGER.info("✓ Using write characteristic 0x%04X and read/notify characteristic 0x%04X", 
                        write_char.handle, read_char.handle)
            
            # Start notifications
            _LOGGER.info("Starting notifications on characteristic 0x%04X...", read_char.handle)
            await client.start_notify(read_char, notification_handler)
            _LOGGER.info("✓ Notifications started successfully")
            
            # Wait a moment for notifications to be set up
            await asyncio.sleep(1.0)  # Increased from 0.5 to 1.0 seconds
            _LOGGER.debug("Notification setup delay complete")
            
            # Test if device is responsive with a simple probe first
            _LOGGER.debug("Testing device responsiveness...")
            test_command = bytes.fromhex("FEFE")  # Simple 2-byte probe
            try:
                await client.write_gatt_char(write_char, test_command)
                _LOGGER.debug("✓ Probe command sent successfully")
            except Exception as e:
                _LOGGER.error("Failed to send probe command: %s", e)
            
            await asyncio.sleep(0.5)  # Brief wait for any response
            
            if response_count > 0:
                _LOGGER.info("✓ Device responded to probe command")
            else:
                _LOGGER.warning("No response to probe command - device may be sleeping or unresponsive")
            
            # Send status request command - try up to 3 times if no response
            # Also try alternative command formats in case the device expects different protocol
            command_variants = [
                ("FEFE03010200", "Standard status command"),
                ("FEFE030102", "Status command without length byte"),
                ("FEFE0301020000", "Status command with padding"),
            ]
            
            for command_attempt in range(3):  # Increased from 2 to 3 attempts
                # Try different command variants on different attempts
                cmd_hex, cmd_desc = command_variants[command_attempt % len(command_variants)]
                command_bytes = bytes.fromhex(cmd_hex)
                
                _LOGGER.info("Sending command attempt %d: %s (%s) to handle 0x%04X", 
                           command_attempt + 1, cmd_hex, cmd_desc, write_char.handle)
                try:
                    await client.write_gatt_char(write_char, command_bytes)
                    _LOGGER.debug("✓ Command sent successfully")
                except Exception as e:
                    _LOGGER.error("Failed to send command: %s", e)
                    continue  # Skip to next attempt if write fails
                
                # Wait for initial response - increased timeout
                initial_wait = 8  # Increased from 3 to 8 seconds for first response
                elapsed = 0
                initial_response_count = response_count
                
                _LOGGER.debug("Waiting up to %ds for response to command %d...", initial_wait, command_attempt + 1)
                while response_count == initial_response_count and elapsed < initial_wait:
                    await asyncio.sleep(0.2)  # Check every 200ms instead of 100ms
                    elapsed += 0.2
                
                if response_count > initial_response_count:
                    _LOGGER.info("✓ Got response on command attempt %d (%s) after %.1fs", 
                               command_attempt + 1, cmd_desc, elapsed)
                    break
                elif command_attempt < 2:  # Don't log for the last attempt
                    _LOGGER.warning("No response to command attempt %d (%s) after %ds, retrying...", 
                                  command_attempt + 1, cmd_desc, initial_wait)
                    await asyncio.sleep(2)  # Increased wait before retry
            
            # Wait for all expected responses (expecting 2 responses total) - increased timeout
            timeout_duration = 20  # Increased from 12 to 20 seconds
            elapsed = 0
            _LOGGER.debug("Waiting up to %ds for all responses (currently have %d)...", timeout_duration, response_count)
            while response_count < 2 and elapsed < timeout_duration:
                await asyncio.sleep(0.2)  # Check every 200ms
                elapsed += 0.2
            
            if response_count == 0:
                _LOGGER.warning("No responses received from Alta 80 within %ds", timeout_duration)
                
                # Try alternative approach: direct read from characteristic
                _LOGGER.info("Trying alternative approach: direct characteristic read...")
                try:
                    # Look for readable characteristics
                    for service in services.services.values():
                        for char in service.characteristics:
                            if 'read' in char.properties:
                                _LOGGER.debug("Attempting to read from characteristic 0x%04X", char.handle)
                                try:
                                    read_data = await client.read_gatt_char(char)
                                    hex_data = read_data.hex().upper()
                                    _LOGGER.info("Direct read from 0x%04X: %s", char.handle, hex_data)
                                    if read_data:
                                        responses.append(hex_data)
                                        response_count += 1
                                except Exception as e:
                                    _LOGGER.debug("Failed to read from 0x%04X: %s", char.handle, e)
                except Exception as e:
                    _LOGGER.debug("Error during direct read attempt: %s", e)
                    
            elif response_count < 2:
                _LOGGER.warning("Only received %d of 2 expected responses from Alta 80", response_count)
            else:
                _LOGGER.info("✓ Received all %d expected responses from Alta 80", response_count)
            
            # Stop notifications
            try:
                await client.stop_notify(read_char)
            except Exception as e:
                _LOGGER.debug("Error stopping notifications: %s", e)
            
            # Parse responses if we got them
            if responses:
                _LOGGER.info("Successfully captured %d responses from Alta 80", len(responses))
                for i, response in enumerate(responses):
                    _LOGGER.debug("Response %d: %s (%d bytes)", i+1, response, len(response)//2)
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
