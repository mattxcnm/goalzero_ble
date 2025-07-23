import asyncio
from bleak import BleakClient, BleakScanner

# Goal Zero device configuration
DEVICE_NAME = "gzf1-80-F14D2A"
WRITE_HANDLE = 0x000A
READ_HANDLE = 0x000C
COMMAND1_PAYLOAD = "FEFE0405010206"
COMMAND2_PAYLOAD = "FEFE0405000205"

# Global variables for response handling
response_count = 0
responses = []

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

async def send_command_sequence():
    """Connect to Goal Zero device and send two commands with delay"""
    global response_count, responses
    
    # Find the device
    device_address = await find_device_by_name(DEVICE_NAME)
    if not device_address:
        return False
    
    print(f"\n🔗 Connecting to {DEVICE_NAME} at {device_address}...")
    
    try:
        async with BleakClient(device_address) as client:
            print("✅ Connected successfully!")
            
            # Find characteristics by handle
            write_char = None
            read_char = None
            
            services = client.services
            for service in services.services.values():
                for char in service.characteristics:
                    if char.handle == WRITE_HANDLE:
                        write_char = char
                        print(f"✅ Found write characteristic at handle 0x{WRITE_HANDLE:04X}")
                    if char.handle == READ_HANDLE:
                        read_char = char
                        print(f"✅ Found read characteristic at handle 0x{READ_HANDLE:04X}")
            
            if not write_char or not read_char:
                print(f"❌ Required handles not found!")
                return False
            
            # Start notifications on the read handle
            print(f"📡 Setting up notifications on handle 0x{READ_HANDLE:04X}")
            await client.start_notify(read_char, notification_handler)
            
            print("\n🚀 Starting command sequence...")
            print("=" * 50)
            
            # Reset response tracking
            response_count = 0
            responses = []
            
            # Send first command
            print(f"📤 Sending Command 1: {COMMAND1_PAYLOAD}")
            command1_bytes = bytes.fromhex(COMMAND1_PAYLOAD)
            await client.write_gatt_char(write_char, command1_bytes)
            
            # Wait for any immediate responses
            await asyncio.sleep(1)
            
            # Wait 3 seconds before second command
            print("⏳ Waiting 3 seconds...")
            await asyncio.sleep(3)
            
            # Send second command
            print(f"📤 Sending Command 2: {COMMAND2_PAYLOAD}")
            command2_bytes = bytes.fromhex(COMMAND2_PAYLOAD)
            await client.write_gatt_char(write_char, command2_bytes)
            
            # Wait for any final responses
            print("⏳ Waiting for final responses...")
            await asyncio.sleep(2)
            
            # Stop notifications
            await client.stop_notify(read_char)
            
            print("=" * 50)
            print(f"✅ Command sequence completed!")
            print(f"📥 Total responses received: {len(responses)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

async def main():
    print("🎯 Goal Zero Command Sequence")
    print("=" * 50)
    print(f"Device: {DEVICE_NAME}")
    print(f"Write Handle: 0x{WRITE_HANDLE:04X}")
    print(f"Read Handle: 0x{READ_HANDLE:04X}")
    print(f"Command 1: {COMMAND1_PAYLOAD}")
    print(f"Command 2: {COMMAND2_PAYLOAD}")
    print(f"Delay: 3 seconds")
    print("=" * 50)
    
    success = await send_command_sequence()
    
    if success:
        print(f"\n📊 SUMMARY:")
        print(f"✅ Command sequence completed successfully")
        print(f"📥 Received {len(responses)} response(s):")
        for i, response in enumerate(responses, 1):
            print(f"   {i}. {response}")
    else:
        print("\n❌ Command sequence failed")

if __name__ == "__main__":
    asyncio.run(main())
