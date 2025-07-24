#!/usr/bin/env python3
"""
Alta 80 Connection Test Script
Tests the improved connection logic with retry mechanisms.
"""

import asyncio
import logging
import sys
from bleak import BleakClient, BleakScanner
import bleak.exc

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

DEVICE_NAME = "gzf1-80-F14D2A"  # Update this to your device name

async def enhanced_device_scan(device_name: str, max_attempts: int = 2):
    """Enhanced device scanning with retry logic - returns device object."""
    device_obj = None
    
    for scan_attempt in range(max_attempts):
        try:
            _LOGGER.info(f"🔍 Scan attempt {scan_attempt + 1}/{max_attempts} for {device_name}")
            
            devices = await BleakScanner.discover(timeout=20.0)
            
            found_devices = []
            for device in devices:
                if device.name:
                    found_devices.append(f"{device.name} ({device.address})")
                    if device.name == device_name:
                        device_obj = device  # Return device object, not address
                        _LOGGER.info(f"✅ Found target device: {device.name} ({device.address})")
                        return device_obj
            
            if scan_attempt == 0:
                _LOGGER.warning(f"❌ Device {device_name} not found on attempt {scan_attempt + 1}")
                _LOGGER.info(f"Found {len(found_devices)} BLE devices: {', '.join(found_devices[:5])}")
                _LOGGER.info("⏳ Waiting 3 seconds before retry...")
                await asyncio.sleep(3)
                
        except Exception as e:
            _LOGGER.error(f"❌ Scan attempt {scan_attempt + 1} failed: {e}")
            if scan_attempt < max_attempts - 1:
                await asyncio.sleep(3)
    
    _LOGGER.error(f"❌ Device {device_name} not found after {max_attempts} attempts")
    return None

async def enhanced_connection_test(device_obj, max_retries: int = 2):
    """Test connection with enhanced retry logic using device object."""
    
    def on_disconnect(client):
        _LOGGER.info(f"🔌 Device {device_obj.name} ({device_obj.address}) disconnected")
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            _LOGGER.info(f"🔗 Connection attempt {attempt + 1}/{max_retries} to {device_obj.name} ({device_obj.address})")
            
            # Use device object for connection
            async with BleakClient(
                device_obj,  # Pass device object, not address string
                timeout=15.0,
                disconnected_callback=on_disconnect
            ) as client:
                _LOGGER.info(f"✅ Connected successfully!")
                
                # Stabilization delay
                _LOGGER.info("⏳ Stabilizing connection...")
                await asyncio.sleep(1.0)
                
                # Test GATT discovery and communication
                success = await test_communication(client)
                return success
                
        except asyncio.TimeoutError as e:
            last_error = e
            _LOGGER.warning(f"⏰ Connection timeout on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                _LOGGER.info("⏳ Waiting 3 seconds before retry...")
                await asyncio.sleep(3)
                
        except bleak.exc.BleakError as e:
            last_error = e
            error_msg = str(e)
            if "ESP_GATT_CONN_FAIL_ESTABLISH" in error_msg:
                _LOGGER.warning(f"📡 BLE connection establishment failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    _LOGGER.info("⏳ Waiting 5 seconds before retry...")
                    await asyncio.sleep(5)
            else:
                _LOGGER.warning(f"📡 BLE error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                    
        except Exception as e:
            last_error = e
            _LOGGER.warning(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
    
    _LOGGER.error(f"❌ All connection attempts failed for {device_obj.name} ({device_obj.address}). Last error: {last_error}")
    return False

async def test_communication(client):
    """Test GATT discovery and communication."""
    try:
        # Discover characteristics
        _LOGGER.info("🔍 Discovering GATT characteristics...")
        
        write_char = None
        read_char = None
        
        services = client.services
        for service in services.services.values():
            _LOGGER.info(f"🔧 Service: {service.uuid}")
            for char in service.characteristics:
                properties = char.properties
                _LOGGER.info(f"   📋 Char: {char.uuid} (0x{char.handle:04X}) - {properties}")
                
                if 'write' in properties or 'write-without-response' in properties:
                    if not write_char:
                        write_char = char
                        _LOGGER.info(f"   ✅ Selected as write characteristic")
                
                if 'notify' in properties or 'indicate' in properties:
                    if not read_char:
                        read_char = char
                        _LOGGER.info(f"   ✅ Selected as notify characteristic")
        
        if not write_char or not read_char:
            _LOGGER.error(f"❌ Missing characteristics: write={write_char is not None}, notify={read_char is not None}")
            return False
        
        # Test communication
        _LOGGER.info("📡 Testing communication...")
        
        responses = []
        response_count = 0
        
        def notification_handler(sender, data):
            nonlocal response_count, responses
            response_count += 1
            hex_data = data.hex().upper()
            _LOGGER.info(f"📥 Response {response_count}: {hex_data}")
            responses.append(hex_data)
        
        # Start notifications
        await client.start_notify(read_char, notification_handler)
        _LOGGER.info("✅ Notifications started")
        
        # Wait for setup
        await asyncio.sleep(0.5)
        
        # Send command with retry
        command_bytes = bytes.fromhex("FEFE03010200")
        
        for cmd_attempt in range(2):
            _LOGGER.info(f"📤 Sending command attempt {cmd_attempt + 1}: FEFE03010200")
            await client.write_gatt_char(write_char, command_bytes)
            
            # Wait for initial response
            initial_count = response_count
            for _ in range(30):  # 3 second wait
                await asyncio.sleep(0.1)
                if response_count > initial_count:
                    break
            
            if response_count > initial_count:
                _LOGGER.info(f"✅ Got response on attempt {cmd_attempt + 1}")
                break
            elif cmd_attempt == 0:
                _LOGGER.warning("⚠️ No response, retrying...")
                await asyncio.sleep(1)
        
        # Wait for all responses
        _LOGGER.info("⏳ Waiting for all responses...")
        for _ in range(120):  # 12 second total wait
            await asyncio.sleep(0.1)
            if response_count >= 2:
                break
        
        await client.stop_notify(read_char)
        _LOGGER.info("✅ Notifications stopped")
        
        if response_count >= 2:
            _LOGGER.info(f"🎉 Success! Received {response_count} responses")
            combined = responses[0] + responses[1] if len(responses) >= 2 else responses[0]
            _LOGGER.info(f"📊 Combined response: {combined} ({len(combined)//2} bytes)")
            return True
        else:
            _LOGGER.warning(f"⚠️ Only received {response_count} responses (expected 2)")
            return False
            
    except Exception as e:
        _LOGGER.error(f"❌ Communication test failed: {e}")
        return False

async def main():
    """Main test function."""
    if len(sys.argv) > 1:
        device_name = sys.argv[1]
    else:
        device_name = DEVICE_NAME
    
    _LOGGER.info(f"🚀 Starting Enhanced Alta 80 Connection Test for: {device_name}")
    _LOGGER.info("=" * 60)
    
    # Step 1: Enhanced device scanning
    device_obj = await enhanced_device_scan(device_name)
    if not device_obj:
        _LOGGER.error("💥 Test failed: Device not found")
        return
    
    # Step 2: Enhanced connection testing
    success = await enhanced_connection_test(device_obj)
    
    if success:
        _LOGGER.info("🎉 Test completed successfully!")
    else:
        _LOGGER.error("💥 Test failed!")

if __name__ == "__main__":
    asyncio.run(main())
