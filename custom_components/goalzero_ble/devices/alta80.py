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
        
        # Bytes to exclude from raw entity creation (replaced with rich entities)
        excluded_bytes = {0, 1, 6, 7, 8, 9, 10, 14, 15, 18, 26, 27, 35}
        
        # Create dual entities for remaining bytes (0-35) - measurement and discrete versions
        # Based on updated byte mapping from protocol analysis
        for i in range(36):
            if i not in excluded_bytes:
                # Regular entity for line graphs
                sensors.append({
                    "key": f"status_byte_{i}",
                    "name": f"Status Byte {i}",
                    "device_class": None,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "unit": None,
                    "icon": "mdi:database"
                })
                
                # Discrete entity for bar charts
                sensors.append({
                    "key": f"status_byte_{i}_discrete",
                    "name": f"Status Byte {i} (Discrete)",
                    "device_class": None,
                    "state_class": None,
                    "unit": None,
                    "icon": "mdi:chart-bar"
                })
        
        # Rich temperature and control sensors
        sensors.extend([
            # Temperature sensors
            {
                "key": "left_zone_temperature",
                "name": "Left Zone Temperature",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": None,  # Will be set dynamically based on B14
                "icon": "mdi:thermometer"
            },
            {
                "key": "right_zone_temperature", 
                "name": "Right Zone Temperature",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": None,  # Will be set dynamically based on B14
                "icon": "mdi:thermometer"
            },
            # Setpoint sensors
            {
                "key": "max_setpoint_temperature",
                "name": "Maximum Setpoint Temperature",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": None,  # Will be set dynamically based on B14
                "icon": "mdi:thermometer-high"
            },
            {
                "key": "min_setpoint_temperature",
                "name": "Minimum Setpoint Temperature", 
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "unit": None,  # Will be set dynamically based on B14
                "icon": "mdi:thermometer-low"
            },
            # Control state sensors
            {
                "key": "eco_mode_status",
                "name": "Eco Mode Status",
                "device_class": None,
                "state_class": None,
                "unit": None,
                "icon": "mdi:leaf"
            },
            {
                "key": "battery_protection_status",
                "name": "Battery Protection Level",
                "device_class": None,
                "state_class": None,
                "unit": None,
                "icon": "mdi:battery-heart"
            },
        ])
        
        return sensors

    def get_buttons(self) -> list[dict[str, Any]]:
        """Return list of button definitions for this device."""
        return [
            {
                "key": "refresh",
                "name": "Refresh Data",
                "icon": "mdi:refresh",
                "command": self._generate_refresh_command,
            },
        ]

    def get_switches(self) -> list[dict[str, Any]]:
        """Return list of switch definitions for this device."""
        return [
            {
                "key": "eco_mode",
                "name": "Eco Mode",
                "icon": "mdi:leaf",
                "command": self._generate_eco_mode_command,
            },
        ]

    def get_selects(self) -> list[dict[str, Any]]:
        """Return list of select definitions for this device."""
        return [
            {
                "key": "battery_protection",
                "name": "Battery Protection",
                "icon": "mdi:battery-heart",
                "options": ["Low", "Medium", "High"],
                "command": self._generate_battery_protection_command,
            },
        ]

    def get_numbers(self) -> list[dict[str, Any]]:
        """Return list of number entity definitions for this device."""
        return [
            {
                "key": "zone1_setpoint",
                "name": "Left Zone Temperature Setpoint",
                "icon": "mdi:thermometer-lines",
                "min_value": None,  # Will be set dynamically based on B10
                "max_value": None,  # Will be set dynamically based on B9
                "step": 1,
                "unit": None,  # Will be set dynamically based on B14
                "mode": "slider",
                "command": self._generate_zone1_setpoint_command,
            },
            {
                "key": "zone2_setpoint",
                "name": "Right Zone Temperature Setpoint",
                "icon": "mdi:thermometer-lines",
                "min_value": None,  # Will be set dynamically based on B10
                "max_value": None,  # Will be set dynamically based on B9
                "step": 1,
                "unit": None,  # Will be set dynamically based on B14
                "mode": "slider",
                "command": self._generate_zone2_setpoint_command,
            },
        ]

    def get_dynamic_number_config(self, key: str) -> dict[str, Any]:
        """Get dynamic configuration for number entities based on current device state."""
        config = {}
        
        if self._data and (key == "zone1_setpoint" or key == "zone2_setpoint"):
            # Get temperature unit from device data
            temp_unit = self._data.get("temperature_unit", "°F")
            min_temp = self._data.get("min_setpoint_temperature")
            max_temp = self._data.get("max_setpoint_temperature")
            
            config["unit"] = UnitOfTemperature.FAHRENHEIT if temp_unit == "°F" else UnitOfTemperature.CELSIUS
            
            # Set limits based on device's min/max values, with fallbacks
            if min_temp is not None:
                config["min_value"] = min_temp
            else:
                config["min_value"] = -4 if temp_unit == "°F" else -20  # Fallback values
                
            if max_temp is not None:
                config["max_value"] = max_temp
            else:
                config["max_value"] = 68 if temp_unit == "°F" else 20  # Fallback values
                
            _LOGGER.debug("Dynamic config for %s: unit=%s, min=%s, max=%s", 
                         key, config["unit"], config["min_value"], config["max_value"])
        
        return config

    def get_dynamic_sensor_config(self, key: str) -> dict[str, Any]:
        """Get dynamic configuration for sensor entities based on current device state."""
        config = {}
        
        # Temperature sensors need dynamic units
        temp_sensors = {
            "left_zone_temperature", "right_zone_temperature",
            "max_setpoint_temperature", "min_setpoint_temperature"
        }
        
        if self._data and key in temp_sensors:
            temp_unit = self._data.get("temperature_unit", "°F")
            config["unit"] = UnitOfTemperature.FAHRENHEIT if temp_unit == "°F" else UnitOfTemperature.CELSIUS
            _LOGGER.debug("Dynamic config for %s: unit=%s", key, config["unit"])
        
        return config

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
        
        # Bytes to exclude from raw entity creation (replaced with rich entities)
        excluded_bytes = {0, 1, 6, 7, 8, 9, 10, 14, 15, 18, 26, 27, 35}
        
        # Initialize remaining status bytes to None
        # Create both regular and discrete versions for each byte
        for i in range(36):
            if i not in excluded_bytes:
                data[f"status_byte_{i}"] = None
                data[f"status_byte_{i}_discrete"] = None
        
        # Initialize rich entity values
        data.update({
            # Control states
            "eco_mode": False,  # From byte 6
            "battery_protection": "Low",  # From byte 7
            "eco_mode_status": "Off",  # Human readable status
            "battery_protection_status": "Low",  # Human readable status
            
            # Temperature setpoints (from bytes 8, 22)
            "zone1_setpoint": None,  # Left zone setpoint
            "zone2_setpoint": None,  # Right zone setpoint
            
            # Temperature readings (from bytes 18, 35)
            "left_zone_temperature": None,  # From byte 18
            "right_zone_temperature": None,  # From byte 35
            
            # System temperature limits (from bytes 9, 10)
            "max_setpoint_temperature": None,  # From byte 9
            "min_setpoint_temperature": None,  # From byte 10
            
            # Temperature unit indicator (from byte 14)
            "temperature_unit": "°F",  # Default to Fahrenheit
            "temperature_unit_code": 0xFE,  # B14 value
        })
        
        return data

    def _parse_status_responses(self, responses: list[str]) -> dict[str, Any]:
        """Parse GATT responses from Alta 80 device into individual bytes."""
        parsed_data = self._get_default_data()
        
        try:
            # Concatenate all responses
            concatenated_response = "".join(responses)
            
            # Convert to bytes
            all_bytes = bytes.fromhex(concatenated_response)
            
            _LOGGER.debug("Parsing %d total bytes from concatenated response", len(all_bytes))
            
            # Bytes to exclude from raw entity creation (replaced with rich entities)
            excluded_bytes = {0, 1, 6, 7, 8, 9, 10, 14, 15, 18, 26, 27, 35}
            
            # First pass: detect temperature unit from byte 14
            temp_unit = "°F"  # Default
            temp_unit_code = 0xFE
            if len(all_bytes) > 14:
                temp_unit_code = all_bytes[14]
                if temp_unit_code == 0xFF:  # 255 = Celsius
                    temp_unit = "°C"
                else:  # 0xFE = 254 = Fahrenheit
                    temp_unit = "°F"
                parsed_data["temperature_unit"] = temp_unit
                parsed_data["temperature_unit_code"] = temp_unit_code
                _LOGGER.debug("Byte 14 (Temperature Unit): %s (raw: 0x%02X)", temp_unit, temp_unit_code)
            
            # Helper function to convert signed byte
            def to_signed(byte_val: int) -> int:
                return byte_val if byte_val <= 127 else byte_val - 256
            
            # Parse each byte individually (exactly 36 bytes)
            for i, byte_val in enumerate(all_bytes):
                if i < 36:  # Exactly 36 bytes in response
                    # Store remaining raw bytes (excluding rich entity bytes)
                    if i not in excluded_bytes:
                        parsed_data[f"status_byte_{i}"] = byte_val
                        parsed_data[f"status_byte_{i}_discrete"] = byte_val
                    
                    # Parse rich entities from specific bytes
                    if i == 6:
                        # Byte 6: Eco Mode (1 = on, 0 = off)
                        parsed_data["eco_mode"] = bool(byte_val == 1)
                        parsed_data["eco_mode_status"] = "On" if byte_val == 1 else "Off"
                        _LOGGER.debug("Byte 6 (Eco Mode): %s (raw: %d)", parsed_data["eco_mode_status"], byte_val)
                        
                    elif i == 7:
                        # Byte 7: Battery Protection (0 = low, 1 = medium, 2 = high)
                        if byte_val == 0:
                            parsed_data["battery_protection"] = "Low"
                            parsed_data["battery_protection_status"] = "Low"
                        elif byte_val == 1:
                            parsed_data["battery_protection"] = "Medium"
                            parsed_data["battery_protection_status"] = "Medium"
                        else:
                            parsed_data["battery_protection"] = "High"
                            parsed_data["battery_protection_status"] = "High"
                        _LOGGER.debug("Byte 7 (Battery Protection): %s (raw: %d)", 
                                    parsed_data["battery_protection_status"], byte_val)
                        
                    elif i == 8:
                        # Byte 8: Left Zone setpoint (signed int)
                        signed_val = to_signed(byte_val)
                        parsed_data["zone1_setpoint"] = signed_val
                        _LOGGER.debug("Byte 8 (Left Zone Setpoint): %d%s (raw: %d)", 
                                    signed_val, temp_unit, byte_val)
                        
                    elif i == 9:
                        # Byte 9: Max setpoint (signed int)
                        signed_val = to_signed(byte_val)
                        parsed_data["max_setpoint_temperature"] = signed_val
                        _LOGGER.debug("Byte 9 (Max Setpoint): %d%s (raw: %d)", 
                                    signed_val, temp_unit, byte_val)
                        
                    elif i == 10:
                        # Byte 10: Min setpoint (signed int)
                        signed_val = to_signed(byte_val)
                        parsed_data["min_setpoint_temperature"] = signed_val
                        _LOGGER.debug("Byte 10 (Min Setpoint): %d%s (raw: %d)", 
                                    signed_val, temp_unit, byte_val)
                        
                    elif i == 18:
                        # Byte 18: Left Zone temperature (signed int)
                        signed_val = to_signed(byte_val)
                        parsed_data["left_zone_temperature"] = signed_val
                        _LOGGER.debug("Byte 18 (Left Zone Temperature): %d%s (raw: %d)", 
                                    signed_val, temp_unit, byte_val)
                        
                    elif i == 22:
                        # Byte 22: Right Zone setpoint (signed int)
                        signed_val = to_signed(byte_val)
                        parsed_data["zone2_setpoint"] = signed_val
                        _LOGGER.debug("Byte 22 (Right Zone Setpoint): %d%s (raw: %d)", 
                                    signed_val, temp_unit, byte_val)
                        
                    elif i == 35:
                        # Byte 35: Right Zone temperature (signed int)
                        signed_val = to_signed(byte_val)
                        parsed_data["right_zone_temperature"] = signed_val
                        _LOGGER.debug("Byte 35 (Right Zone Temperature): %d%s (raw: %d)", 
                                    signed_val, temp_unit, byte_val)
            
            # Validate expected response length
            if len(all_bytes) != 36:
                _LOGGER.warning("Expected 36 bytes, got %d bytes in response", len(all_bytes))
            
            _LOGGER.debug("Successfully parsed all 36 status bytes with rich entities")
            
        except Exception as e:
            _LOGGER.error("Error parsing Alta 80 status responses: %s", e)
        
        return parsed_data

    def parse_ble_data(self, data: bytes) -> dict[str, Any]:
        """Parse BLE data specific to Alta 80 fridge system."""
        # Convert single data packet to hex string format for consistency
        hex_data = data.hex().upper()
        return self._parse_status_responses([hex_data])
    
    # Control command methods for Alta 80
    
    def create_zone1_temp_command(self, temp_f: int) -> bytes:
        """Create Zone 1 temperature setpoint command.
        
        Args:
            temp_f: Temperature in Fahrenheit (-4 to 68)
            
        Returns:
            Command bytes to send
        """
        temp_f = max(-4, min(68, temp_f))  # Clamp to valid range
        temp_hex = temp_f & 0xFF  # Handle negative temps with 2's complement
        checksum = (0x04 + 0x05 + temp_hex + 0x02) & 0xFF
        
        command = bytes([0xFE, 0xFE, 0x04, 0x05, temp_hex, 0x02, checksum])
        _LOGGER.debug("Zone 1 temp command for %d°F: %s", temp_f, command.hex(':'))
        return command
    
    def create_zone2_temp_command(self, temp_f: int) -> bytes:
        """Create Zone 2 temperature setpoint command.
        
        Args:
            temp_f: Temperature in Fahrenheit (-4 to 68)
            
        Returns:
            Command bytes to send
        """
        temp_f = max(-4, min(68, temp_f))  # Clamp to valid range
        temp_hex = temp_f & 0xFF
        checksum = (0x04 + 0x06 + temp_hex + 0x02) & 0xFF
        
        command = bytes([0xFE, 0xFE, 0x04, 0x06, temp_hex, 0x02, checksum])
        _LOGGER.debug("Zone 2 temp command for %d°F: %s", temp_f, command.hex(':'))
        return command
    
    def create_eco_mode_command(self, enabled: bool) -> bytes:
        """Create eco mode on/off command.
        
        Args:
            enabled: True to enable eco mode, False to disable
            
        Returns:
            Command bytes to send
        """
        eco_byte = 0x02 if enabled else 0x01
        command = bytes([0xFE, 0xFE, 0x21, eco_byte, 0x00, 0x01, 0x00, 0x00, 0x00, 0x44,
                        0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x03, 0x64])
        
        _LOGGER.debug("Eco mode command (%s): %s", "ON" if enabled else "OFF", command.hex(':'))
        return command
    
    def create_battery_protection_command(self, level: str) -> bytes:
        """Create battery protection level command.
        
        Args:
            level: "low", "med", or "high"
            
        Returns:
            Command bytes to send
        """
        level_map = {
            "low": 0x00,
            "med": 0x01,
            "high": 0x02
        }
        
        if level not in level_map:
            raise ValueError(f"Level must be 'low', 'med', or 'high', got: {level}")
        
        level_byte = level_map[level]
        command = bytes([0xFE, 0xFE, 0x21, 0x02, 0x00, 0x01, 0x01, level_byte, 0x00, 0x44,
                        0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x03, 0x64])
        
        _LOGGER.debug("Battery protection command (%s): %s", level, command.hex(':'))
        return command
    
    def create_button_command(self, button_key: str, **kwargs) -> bytes:
        """Create command for button press.
        
        Args:
            button_key: The button key identifier
            **kwargs: Additional parameters (e.g., current_temp for temp adjustment buttons)
            
        Returns:
            Command bytes to send
        """
        if button_key == "zone1_temp_up":
            current_temp = kwargs.get("current_temp", 32)  # Default to 32°F if unknown
            return self.create_zone1_temp_command(current_temp + 1)
        
        elif button_key == "zone1_temp_down":
            current_temp = kwargs.get("current_temp", 32)
            return self.create_zone1_temp_command(current_temp - 1)
            
        elif button_key == "zone2_temp_up":
            current_temp = kwargs.get("current_temp", 32)
            return self.create_zone2_temp_command(current_temp + 1)
            
        elif button_key == "zone2_temp_down":
            current_temp = kwargs.get("current_temp", 32)
            return self.create_zone2_temp_command(current_temp - 1)
            
        elif button_key == "toggle_eco_mode":
            current_eco = kwargs.get("current_eco_mode", False)
            return self.create_eco_mode_command(not current_eco)
            
        elif button_key == "cycle_battery_protection":
            current_level = kwargs.get("current_battery_protection", "low")
            level_cycle = {"low": "med", "med": "high", "high": "low"}
            next_level = level_cycle.get(current_level, "low")
            return self.create_battery_protection_command(next_level)
        
        else:
            raise ValueError(f"Unknown button key: {button_key}")
    
    def create_number_set_command(self, number_key: str, value: float) -> bytes:
        """Create command for number entity value change.
        
        Args:
            number_key: The number entity key identifier
            value: The new value to set
            
        Returns:
            Command bytes to send
        """
        if number_key == "zone1_setpoint":
            return self.create_zone1_temp_command(int(value))
        elif number_key == "zone2_setpoint":
            return self.create_zone2_temp_command(int(value))
        else:
            raise ValueError(f"Unknown number key: {number_key}")

    def create_switch_command(self, switch_key: str, state: bool) -> bytes:
        """Create command for switch entity state change.
        
        Args:
            switch_key: The switch entity key identifier
            state: The new state (True for on, False for off)
            
        Returns:
            Command bytes to send
        """
        if switch_key == "power":
            # Create power on/off command
            if state:
                # Power on command - needs to be determined from device analysis
                command = bytes([0xFE, 0xFE, 0x21, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x44,
                               0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x03, 0x65])
            else:
                # Power off command - needs to be determined from device analysis
                command = bytes([0xFE, 0xFE, 0x21, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x44,
                               0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x03, 0x64])
            _LOGGER.debug("Power command (%s): %s", "ON" if state else "OFF", command.hex(':'))
            return command
            
        elif switch_key == "eco_mode":
            return self.create_eco_mode_command(state)
        else:
            raise ValueError(f"Unknown switch key: {switch_key}")

    def create_select_command(self, select_key: str, option: str) -> bytes:
        """Create command for select entity option change.
        
        Args:
            select_key: The select entity key identifier
            option: The new option value
            
        Returns:
            Command bytes to send
        """
        if select_key == "battery_protection":
            return self.create_battery_protection_command(option)
        else:
            raise ValueError(f"Unknown select key: {select_key}")

    async def send_command(self, ble_manager, command: bytes) -> bool:
        """Send a command to the Alta 80 device with extra debug logging."""
        try:
            command_hex = command.hex(':')
            _LOGGER.info("[Alta80] Attempting to send command: %s (%d bytes)", command_hex, len(command))
            _LOGGER.info("[Alta80] Device name: %s, address: %s", self.name, self.address)
            _LOGGER.info("[Alta80] BLE manager type: %s", type(ble_manager).__name__)
            if hasattr(ble_manager, 'is_connected'):
                _LOGGER.info("[Alta80] BLE manager connection status: %s", ble_manager.is_connected)
            else:
                _LOGGER.warning("[Alta80] BLE manager missing is_connected property")
            available_methods = [method for method in dir(ble_manager) if not method.startswith('_')]
            _LOGGER.debug("[Alta80] BLE manager available methods: %s", available_methods)
            # Use the correct method name for sending commands
            if hasattr(ble_manager, 'send_command_to_device'):
                _LOGGER.info("[Alta80] Using send_command_to_device method")
                success = await ble_manager.send_command_to_device(self.name, command)
            elif hasattr(ble_manager, 'send_command'):
                _LOGGER.info("[Alta80] Using send_command method")
                success = await ble_manager.send_command(command)
            else:
                _LOGGER.error("[Alta80] No suitable send command method found on BLE manager")
                return False
            if success:
                _LOGGER.info("[Alta80] Command sent successfully!")
            else:
                _LOGGER.error("[Alta80] Command send failed!")
            return success
        except Exception as e:
            _LOGGER.error("[Alta80] Exception sending command: %s", e)
            import traceback
            _LOGGER.error("[Alta80] Traceback: %s", traceback.format_exc())
            return False
    
    # Command generation methods for entity platforms
    
    def _generate_eco_mode_command(self, enabled: bool) -> bytes:
        """Generate eco mode command for switch entity."""
        return self.create_eco_mode_command(enabled)
    
    def _generate_battery_protection_command(self, level: str) -> bytes:
        """Generate battery protection command for select entity."""
        # Map Home Assistant option names to command values
        level_map = {
            "Low": "low",
            "Medium": "med", 
            "High": "high"
        }
        command_level = level_map.get(level, "low")
        return self.create_battery_protection_command(command_level)
    
    def _generate_zone1_setpoint_command(self, temp_f: float) -> bytes:
        """Generate Zone 1 setpoint command for number entity."""
        return self.create_zone1_temp_command(int(temp_f))
    
    def _generate_zone2_setpoint_command(self, temp_f: float) -> bytes:
        """Generate Zone 2 setpoint command for number entity."""
        return self.create_zone2_temp_command(int(temp_f))
    
    def _generate_refresh_command(self) -> bytes:
        """Generate refresh command for button entity."""
        # Return status request command
        return bytes([0xFE, 0xFE, 0x03, 0x01, 0x02, 0x00])
