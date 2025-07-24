#!/usr/bin/env python3
"""
Diagnostic tool for Goal Zero BLE devices.
This script helps debug connection and GATT issues.
"""

import asyncio
import logging
import sys
from bleak import BleakClient, BleakScanner

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)


async def scan_for_devices():
    """Scan for Goal Zero devices."""
    _LOGGER.info("Scanning for Goal Zero devices...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    goalzero_devices = []
    for device in devices:
        if device.name and ('gzf1-80-' in device.name or 'gzy5c-' in device.name):
            goalzero_devices.append(device)
            _LOGGER.info(f"Found Goal Zero device: {device.name} ({device.address})")
    
    return goalzero_devices


async def diagnose_device(device_address: str | None = None, device_name: str | None = None):
    """Perform diagnostic tests on a specific device."""
    _LOGGER.info(f"Starting diagnostics for {device_name or device_address}")
    
    try:
        # If we have device_name, scan for it; if we have address, find device by address
        device_obj = None
        
        if device_name:
            _LOGGER.info("Scanning for device by name...")
            devices = await BleakScanner.discover(timeout=15.0)
            for device in devices:
                if device.name == device_name:
                    device_obj = device
                    _LOGGER.info(f"✓ Found device by name: {device.name} ({device.address})")
                    break
        elif device_address:
            _LOGGER.info("Finding device by address...")
            device_obj = await BleakScanner.find_device_by_address(device_address, timeout=15.0)
            if device_obj:
                _LOGGER.info(f"✓ Found device by address: {device_obj.name or 'Unknown'} ({device_obj.address})")
        
        if not device_obj:
            _LOGGER.error(f"✗ Device not found")
            return
        
        # Test connection using device object
        _LOGGER.info("Testing connection...")
        async with BleakClient(device_obj, timeout=15.0) as client:
            _LOGGER.info(f"✓ Successfully connected to {device_obj.address}")
            
            # Discover services
            _LOGGER.info("Discovering GATT services...")
            services = client.services
            
            _LOGGER.info("=== GATT Services ===")
            for service in services.services.values():
                _LOGGER.info(f"Service: {service.uuid}")
                for char in service.characteristics:
                    _LOGGER.info(
                        f"  Characteristic: {char.uuid} (Handle: 0x{char.handle:04X}, Properties: {char.properties})"
                    )
                    for descriptor in char.descriptors:
                        _LOGGER.info(f"    Descriptor: {descriptor.uuid} (Handle: 0x{descriptor.handle:04X})")
            
            # Test Alta 80 specific handles if this looks like an Alta 80
            if device_obj.name and 'gzf1-80-' in device_obj.name:
                await test_alta80_communication(client)
            
        _LOGGER.info("✓ Diagnostic completed successfully")
        
    except asyncio.TimeoutError:
        _LOGGER.error(f"✗ Connection timeout for {device_address}")
    except Exception as e:
        _LOGGER.error(f"✗ Error during diagnostics: {e}")


async def test_alta80_communication(client):
    """Test specific Alta 80 communication."""
    _LOGGER.info("Testing Alta 80 specific communication...")
    
    # Find characteristics by properties instead of hardcoded handles
    write_char = None
    read_char = None
    
    services = client.services
    _LOGGER.info("Discovering characteristics by properties...")
    
    for service in services.services.values():
        for char in service.characteristics:
            properties = char.properties
            if 'write' in properties or 'write-without-response' in properties:
                if not write_char:  # Take the first one found
                    write_char = char
                    _LOGGER.info(f"✓ Found write characteristic at handle 0x{char.handle:04X} with properties {properties}")
            
            if 'notify' in properties or 'indicate' in properties:
                if not read_char:  # Take the first one found
                    read_char = char
                    _LOGGER.info(f"✓ Found notify characteristic at handle 0x{char.handle:04X} with properties {properties}")
    
    if not write_char:
        _LOGGER.error("✗ No write characteristic found")
        return
    
    if not read_char:
        _LOGGER.error("✗ No notify characteristic found")
        return
    
    # Test command sending with retry logic
    try:
        responses = []
        response_count = 0
        
        def notification_handler(sender, data):
            nonlocal response_count, responses
            response_count += 1
            hex_data = data.hex().upper()
            _LOGGER.info(f"Response {response_count}: {hex_data}")
            responses.append(hex_data)
        
        # Start notifications
        await client.start_notify(read_char, notification_handler)
        _LOGGER.info("✓ Started notifications")
        
        # Wait for notifications to be set up
        await asyncio.sleep(0.5)
        
        # Send status command with retry logic
        command_bytes = bytes.fromhex("FEFE03010200")
        
        for attempt in range(2):
            _LOGGER.info(f"✓ Sending status command attempt {attempt + 1}: FEFE03010200")
            await client.write_gatt_char(write_char, command_bytes)
            
            # Wait for initial response
            initial_wait = 3
            elapsed = 0
            initial_response_count = response_count
            
            while response_count == initial_response_count and elapsed < initial_wait:
                await asyncio.sleep(0.1)
                elapsed += 0.1
            
            if response_count > initial_response_count:
                _LOGGER.info(f"✓ Got response on attempt {attempt + 1}")
                break
            elif attempt == 0:
                _LOGGER.warning("⚠ No response to first command, retrying...")
                await asyncio.sleep(1)
        
        # Wait for all responses
        timeout_duration = 12
        elapsed = 0
        while response_count < 2 and elapsed < timeout_duration:
            await asyncio.sleep(0.1)
            elapsed += 0.1
        
        await client.stop_notify(read_char)
        _LOGGER.info("✓ Stopped notifications")
        
        if response_count >= 2:
            _LOGGER.info(f"✓ Received {response_count} responses as expected")
            
            # Concatenate and analyze
            if len(responses) >= 2:
                combined = responses[0] + responses[1]
                _LOGGER.info(f"Combined response: {combined}")
                _LOGGER.info(f"Combined length: {len(combined)//2} bytes")
                
                if len(combined) == 72:  # 36 bytes * 2 hex chars
                    _LOGGER.info("✓ Response length matches expected 36 bytes")
                else:
                    _LOGGER.warning(f"⚠ Unexpected response length: {len(combined)//2} bytes (expected 36)")
        else:
            _LOGGER.warning(f"⚠ Only received {response_count} responses (expected 2)")
        
    except Exception as e:
        _LOGGER.error(f"✗ Error testing communication: {e}")


async def main():
    """Main diagnostic function."""
    if len(sys.argv) > 1:
        # First arg could be address or device name
        first_arg = sys.argv[1]
        second_arg = sys.argv[2] if len(sys.argv) > 2 else None
        
        # Try to determine if first arg is MAC address or device name
        if ':' in first_arg or len(first_arg.replace('-', '').replace(':', '')) == 12:
            # Looks like MAC address
            await diagnose_device(device_address=first_arg, device_name=second_arg)
        else:
            # Looks like device name
            await diagnose_device(device_name=first_arg)
    else:
        # Scan and diagnose all found devices
        devices = await scan_for_devices()
        
        if not devices:
            _LOGGER.warning("No Goal Zero devices found")
            return
        
        for device in devices:
            await diagnose_device(device_name=device.name)
            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
