#!/usr/bin/env python3
"""
Updated Goal Zero GATT testing script with dynamic handle discovery.
This version discovers GATT characteristics by properties instead of hardcoded handles.
"""

import asyncio
import csv
import datetime
from bleak import BleakClient, BleakScanner

# Goal Zero device configuration
DEVICE_NAME = "gzf1-80-F14D2A"
COMMAND_PAYLOAD = "FEFE03010200"

# Global variables for response handling
response_count = 0
responses = []
csv_data = []

async def find_device_by_name(device_name):
    """Find device by exact name match"""
    print(f"🔍 Scanning for device: {device_name}")
    devices = await BleakScanner.discover(timeout=10.0)
    
    for device in devices:
        if device.name == device_name:
            print(f"✅ Found device: {device.name} ({device.address})")
            return device.address
    
    print(f"❌ Device '{device_name}' not found")
    print("Available devices:")
    for device in devices:
        print(f"  - {device.name or 'Unknown'} ({device.address})")
    return None

def notification_handler(sender, data):
    """Handle notifications from the device"""
    global response_count, responses
    response_count += 1
    hex_data = data.hex().upper()
    print(f"📥 Response {response_count}: {hex_data}")
    responses.append(hex_data)

async def wait_for_responses(expected_count=2, timeout=5):
    """Wait for a specific number of responses with timeout"""
    global response_count
    elapsed = 0
    
    while response_count < expected_count and elapsed < timeout:
        await asyncio.sleep(0.1)
        elapsed += 0.1
    
    return response_count >= expected_count

def parse_combined_response(combined_hex):
    """Parse the combined response into individual bytes"""
    print(f"\n📊 PARSING COMBINED RESPONSE:")
    print(f"Combined hex: {combined_hex}")
    print(f"Total length: {len(combined_hex)//2} bytes")
    
    if len(combined_hex) != 72:  # Should be 36 bytes = 72 hex characters
        print(f"⚠️  WARNING: Expected 72 hex characters (36 bytes), got {len(combined_hex)}")
    
    # Parse into individual bytes
    for i in range(0, len(combined_hex), 2):
        byte_index = i // 2
        byte_value = combined_hex[i:i+2]
        decimal_value = int(byte_value, 16)
        print(f"Byte {byte_index:2d}: 0x{byte_value} ({decimal_value:3d})")
        
        # Add special parsing for known bytes
        if byte_index == 18:
            print(f"         -> Zone 1 Temp: {decimal_value}°C")
        elif byte_index == 34:
            temp_high_res = decimal_value / 10.0
            print(f"         -> Zone 2 Temp (High Res): {temp_high_res}°C")
        elif byte_index == 35:
            exceeded = "YES" if decimal_value & 0x01 else "NO"
            print(f"         -> Zone 1 Setpoint Exceeded: {exceeded}")

async def discover_gatt_characteristics(client):
    """Discover GATT characteristics by properties"""
    print("\n🔍 DISCOVERING GATT CHARACTERISTICS BY PROPERTIES:")
    
    write_char = None
    notify_char = None
    
    services = client.services
    for service in services.services.values():
        print(f"\n🔧 Service: {service.uuid}")
        for char in service.characteristics:
            properties = char.properties
            print(f"   Characteristic: {char.uuid} (Handle: 0x{char.handle:04X}, Properties: {properties})")
            
            # Look for write characteristic
            if 'write' in properties or 'write-without-response' in properties:
                if not write_char:
                    write_char = char
                    print(f"      -> Selected as WRITE characteristic")
            
            # Look for notify characteristic  
            if 'notify' in properties or 'indicate' in properties:
                if not notify_char:
                    notify_char = char
                    print(f"      -> Selected as NOTIFY characteristic")
    
    return write_char, notify_char

async def test_goal_zero_device():
    """Test communication with Goal Zero device using dynamic discovery"""
    global response_count, responses
    
    device_address = await find_device_by_name(DEVICE_NAME)
    if not device_address:
        return False
    
    try:
        print(f"\n🔗 Connecting to {DEVICE_NAME} at {device_address}")
        
        async with BleakClient(device_address, timeout=12.0) as client:
            print(f"✅ Connected to {DEVICE_NAME}")
            
            # Discover characteristics dynamically
            write_char, notify_char = await discover_gatt_characteristics(client)
            
            if not write_char:
                print("❌ No write characteristic found!")
                return False
            
            if not notify_char:
                print("❌ No notify characteristic found!")
                return False
            
            print(f"\n✅ Using write characteristic: 0x{write_char.handle:04X}")
            print(f"✅ Using notify characteristic: 0x{notify_char.handle:04X}")
            
            # Reset response tracking
            response_count = 0
            responses = []
            
            # Set up notifications
            print(f"\n📡 Setting up notifications on handle 0x{notify_char.handle:04X}")
            await client.start_notify(notify_char, notification_handler)
            
            # Send command
            print(f"📤 Sending command: {COMMAND_PAYLOAD}")
            command_bytes = bytes.fromhex(COMMAND_PAYLOAD)
            await client.write_gatt_char(write_char, command_bytes)
            
            # Wait for responses
            print("⏳ Waiting for responses...")
            success = await wait_for_responses(expected_count=2, timeout=8)
            
            # Stop notifications
            await client.stop_notify(notify_char)
            
            if success:
                print(f"\n✅ Received {response_count} responses successfully!")
                
                # Combine responses
                if len(responses) >= 2:
                    combined = responses[0] + responses[1]
                    parse_combined_response(combined)
                    
                    # Save to CSV
                    timestamp = datetime.datetime.now().isoformat()
                    csv_data.append({
                        'timestamp': timestamp,
                        'device': DEVICE_NAME,
                        'response1': responses[0],
                        'response2': responses[1],
                        'combined': combined,
                        'write_handle': f"0x{write_char.handle:04X}",
                        'notify_handle': f"0x{notify_char.handle:04X}"
                    })
                    
                    # Write to CSV file
                    filename = f"alta80_dynamic_handles_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    with open(filename, 'w', newline='') as csvfile:
                        fieldnames = ['timestamp', 'device', 'response1', 'response2', 'combined', 'write_handle', 'notify_handle']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(csv_data)
                    
                    print(f"\n💾 Data saved to {filename}")
                
                return True
            else:
                print(f"\n❌ Only received {response_count} responses (expected 2)")
                return False
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

async def main():
    """Main function"""
    print("🚀 Goal Zero BLE Test with Dynamic Handle Discovery")
    print("=" * 50)
    
    success = await test_goal_zero_device()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")

if __name__ == "__main__":
    asyncio.run(main())
