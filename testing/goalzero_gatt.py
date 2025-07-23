import asyncio
from bleak import BleakClient, BleakScanner

# Goal Zero device configuration
DEVICE_NAME = "gzf1-80-F14D2A"
WRITE_HANDLE = 0x000A  # Updated based on GATT discovery
READ_HANDLE = 0x000C   # Updated based on GATT discovery
COMMAND_PAYLOAD = "FEFE03010200"

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

async def discover_gatt_services(client):
    """Discover and print all GATT services, characteristics, and handles"""
    print("\n🔍 DISCOVERING GATT SERVICES AND HANDLES:")
    print("=" * 60)
    
    services = client.services
    service_list = list(services.services.values())
    
    for service in service_list:
        print(f"\n🔧 Service: {service.uuid}")
        print(f"   Handle: 0x{service.handle:04X}")
        
        for char in service.characteristics:
            properties = ", ".join(char.properties)
            print(f"   📡 Characteristic: {char.uuid}")
            print(f"      Handle: 0x{char.handle:04X}")
            print(f"      Properties: {properties}")
            
            # List descriptors with handles
            for descriptor in char.descriptors:
                print(f"      📝 Descriptor: {descriptor.uuid}")
                print(f"         Handle: 0x{descriptor.handle:04X}")
    
    print("=" * 60)

async def send_gatt_command():
    """Connect to Goal Zero device and send GATT command"""
    global response_count, responses
    
    # Reset response tracking
    response_count = 0
    responses = []
    
    # Find the device
    device_address = await find_device_by_name(DEVICE_NAME)
    if not device_address:
        return False
    
    print(f"\n🔗 Connecting to {DEVICE_NAME} at {device_address}...")
    
    try:
        async with BleakClient(device_address) as client:
            print("✅ Connected successfully!")
            
            # First, discover all services and handles
            await discover_gatt_services(client)
            
            # Try to find characteristics by handle
            write_char = None
            read_char = None
            
            services = client.services
            for service in services.services.values():
                for char in service.characteristics:
                    if char.handle == WRITE_HANDLE:
                        write_char = char
                        print(f"✅ Found write characteristic at handle 0x{WRITE_HANDLE:04X}: {char.uuid}")
                    if char.handle == READ_HANDLE:
                        read_char = char
                        print(f"✅ Found read characteristic at handle 0x{READ_HANDLE:04X}: {char.uuid}")
            
            if not write_char:
                print(f"❌ Write handle 0x{WRITE_HANDLE:04X} not found!")
                return False
                
            if not read_char:
                print(f"❌ Read handle 0x{READ_HANDLE:04X} not found!")
                print("💡 Try using a different handle from the list above")
                return False
            
            # Start notifications on the read handle
            print(f"\n📡 Setting up notifications on handle 0x{READ_HANDLE:04X}")
            await client.start_notify(read_char, notification_handler)
            
            # Send the command to the write handle
            command_bytes = bytes.fromhex(COMMAND_PAYLOAD)
            print(f"📤 Sending command to handle 0x{WRITE_HANDLE:04X}: {COMMAND_PAYLOAD}")
            await client.write_gatt_char(write_char, command_bytes)
            
            # Wait for two responses
            print("⏳ Waiting for two responses...")
            timeout = 10  # seconds
            elapsed = 0
            
            while response_count < 2 and elapsed < timeout:
                await asyncio.sleep(0.1)
                elapsed += 0.1
            
            if response_count >= 2:
                print(f"✅ Received {response_count} responses!")
            else:
                print(f"⚠️ Only received {response_count} response(s) within {timeout} seconds")
            
            # Stop notifications
            await client.stop_notify(read_char)
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

async def main():
    print("🎯 Goal Zero GATT Command Test")
    print("=" * 50)
    print(f"Device: {DEVICE_NAME}")
    print(f"Write Handle: 0x{WRITE_HANDLE:04X}")
    print(f"Read Handle: 0x{READ_HANDLE:04X}")
    print(f"Command: {COMMAND_PAYLOAD}")
    print("=" * 50)
    
    success = await send_gatt_command()
    
    if success:
        print("\n📊 SUMMARY:")
        print(f"✅ Command sent successfully")
        print(f"📥 Received {len(responses)} response(s):")
        for i, response in enumerate(responses, 1):
            print(f"   {i}. {response}")
    else:
        print("\n❌ Command failed")

if __name__ == "__main__":
    asyncio.run(main())
