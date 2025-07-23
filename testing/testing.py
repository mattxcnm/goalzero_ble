import asyncio
from bleak import BleakClient, BleakScanner

from dotenv import load_dotenv
import os

load_dotenv()

# Goal Zero device configuration
DEVICE_NAME = "gzf1-80-F14D2A"
WRITE_HANDLE = 0x000B
READ_HANDLE = 0x000D
COMMAND_PAYLOAD = "FEFE03010200"

# Global variables for response handling
response_count = 0
responses = []

async def find_goalzero_device(custom_name_pattern=None):
    """Find Goal Zero device by scanning for BLE devices"""
    print("Scanning for Goal Zero device...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    # Use custom pattern if provided, otherwise default patterns
    patterns = [custom_name_pattern] if custom_name_pattern else ["goal", "zero", "goalzero"]
    
    for device in devices:
        # Check if device name contains specified patterns
        device_name = device.name or ""
        if any(pattern.lower() in device_name.lower() for pattern in patterns if pattern):
            print(f"Found potential Goal Zero device: {device_name} ({device.address})")
            return device.address
    
    # If no device found by name, list all available devices for debugging
    print("No Goal Zero device found with specified patterns. Available devices:")
    for device in devices:
        print(f"  - {device.name or 'Unknown'} ({device.address})")
    
    return None

async def discover_device_services(device_address):
    """Discover and list all services and characteristics for a device"""
    print(f"\n� Discovering services and characteristics for {device_address}...")
    try:
        async with BleakClient(device_address) as client:
            print(f"✅ Connected to device!")
            
            services = client.services
            service_list = list(services.services.values())
            print(f"\n📋 Found {len(service_list)} services:")
            
            for service in service_list:
                print(f"\n🔧 Service: {service.uuid}")
                print(f"   Description: {service.description}")
                
                for char in service.characteristics:
                    properties = ", ".join(char.properties)
                    print(f"   📡 Characteristic: {char.uuid}")
                    print(f"      Properties: {properties}")
                    if char.description:
                        print(f"      Description: {char.description}")
                    
                    # List descriptors if any
                    for descriptor in char.descriptors:
                        print(f"      📝 Descriptor: {descriptor.uuid}")
            
            return services
            
    except Exception as e:
        print(f"❌ Failed to discover services: {str(e)}")
        return None

async def send_command(client, hex_str):
    data = bytes.fromhex(hex_str)
    await client.write_gatt_char(CHAR_UUID, data)
    print(f"Sent: {hex_str}")

def parse_temp_segment(seg: bytes) -> float:
    # change divisor based on calibration; example: value / 100
    raw = int.from_bytes(seg, byteorder='little', signed=True)
    return raw / 100

def parse_response(data: bytes):
    # assumes “FEFE … 44 FC 04 …” contains two 4‑byte temps after byte 4
    fridge_raw = data[4:8]
    freezer_raw = data[8:12]
    print(">>> Fridge:", parse_temp_segment(fridge_raw), "°C",
          "| Freezer:", parse_temp_segment(freezer_raw), "°C")

async def test_connection(device_address, method_name):
    """Test connection to a device and return success status"""
    try:
        print(f"\n🔗 Testing connection via {method_name} to {device_address}...")
        async with BleakClient(device_address) as client:
            if client.is_connected:
                print(f"✅ {method_name}: Successfully connected!")
                return True
            else:
                print(f"❌ {method_name}: Failed to connect")
                return False
    except Exception as e:
        print(f"❌ {method_name}: Connection failed - {str(e)}")
        return False

async def main():
    print("🎯 Goal Zero BLE Connection Test")
    print("=" * 50)
    
    successful_address = None
    successful_method = None
    
    # Method 1: Try environment variable address
    print("\n📍 METHOD 1: Using environment variable address")
    if gz_address:
        print(f"Found goalzero_address in environment: {gz_address}")
        if await test_connection(gz_address, "Environment Address"):
            successful_address = gz_address
            successful_method = "Environment Address"
    else:
        print("❌ No goalzero_address found in environment variables")
    
    # Method 2: Try discovery by default patterns (goal, zero, goalzero)
    if not successful_address:
        print("\n🔍 METHOD 2: Device discovery by default patterns")
        discovered_address = await find_goalzero_device()
        if discovered_address:
            if await test_connection(discovered_address, "Auto-Discovery (default patterns)"):
                successful_address = discovered_address
                successful_method = "Auto-Discovery (default patterns)"
        else:
            print("❌ No device found using default patterns")
    
    # Method 3: Try custom device name pattern
    if not successful_address and gz_name:
        print(f"\n🏷️  METHOD 3: Device discovery by custom name pattern")
        print(f"Using custom pattern: {gz_name}")
        custom_discovered = await find_goalzero_device(gz_name)
        if custom_discovered:
            if await test_connection(custom_discovered, f"Custom Pattern ({gz_name})"):
                successful_address = custom_discovered
                successful_method = f"Custom Pattern ({gz_name})"
        else:
            print("❌ No device found using custom pattern")
    elif not successful_address:
        print("\n🏷️  METHOD 3: Skipped (no goalzero_device_name set)")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 CONNECTION TEST SUMMARY:")
    if successful_address:
        print(f"✅ SUCCESS! Connected via: {successful_method}")
        print(f"📍 Device Address: {successful_address}")
        
        # Discover services and characteristics
        await discover_device_services(successful_address)
        
        # Ask user if they want to proceed with commands
        print(f"\n❓ The current characteristic UUID is: {gz_uuid}")
        print("❓ Would you like to proceed with Goal Zero commands using this UUID?")
        print("   (Press Ctrl+C to stop or check the discovered characteristics above)")
        
        try:
            # Proceed with the actual commands
            print(f"\n🚀 Proceeding with Goal Zero commands...")
            await run_goalzero_commands(successful_address)
        except Exception as e:
            print(f"❌ Command execution failed: {str(e)}")
            print("💡 Check the discovered characteristics above for the correct UUID")
    else:
        print("❌ ALL CONNECTION METHODS FAILED")
        print("\n💡 Troubleshooting tips:")
        print("1. Ensure Goal Zero device is powered on and in range")
        print("2. Check Bluetooth is enabled on your computer") 
        print("3. Try setting these environment variables:")
        print("   - goalzero_address (if you know the exact MAC address)")
        print("   - goalzero_device_name (exact device name)")
        print("   - goalzero_char_uuid (required for commands)")

async def run_goalzero_commands(device_address):
    """Run the actual Goal Zero commands once connected"""
    print(f"Connecting to device at {device_address} for command execution...")
    
    async with BleakClient(device_address) as client:
        await client.start_notify(CHAR_UUID, lambda _, d: parse_response(d))

        # Example command sequence
        cmds = {
            "left_down":    "FEFE040501020600",
            "left_up":      "FEFE040500020500",
            "right_down":   "FEFE040624022A00",
            "right_up":     "FEFE040623022900",
            # ...
        }
        for name, cmd in cmds.items():
            print("**", name)
            await send_command(client, cmd)
            await asyncio.sleep(1)

        # Let notifications flow for a bit
        await asyncio.sleep(5)
        await client.stop_notify(CHAR_UUID)

if __name__ == "__main__":
    asyncio.run(main())