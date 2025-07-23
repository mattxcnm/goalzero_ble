import asyncio
import csv
import datetime
from bleak import BleakClient, BleakScanner

# Goal Zero device configuration
DEVICE_NAME = "gzf1-80-F14D2A"
WRITE_HANDLE = 0x000A  # Updated based on GATT discovery
READ_HANDLE = 0x000C   # Updated based on GATT discovery
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

def save_to_csv(filename="goalzero_responses.csv"):
    """Save all collected data to CSV file"""
    print(f"\n💾 Saving {len(csv_data)} records to {filename}")
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'command', 'response1', 'response2', 'concatenated_response']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in csv_data:
            writer.writerow(row)
    
    print(f"✅ Data saved to {filename}")

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
    """Connect to Goal Zero device and continuously monitor for 5 minutes"""
    global response_count, responses, csv_data
    
    # Find the device
    device_address = await find_device_by_name(DEVICE_NAME)
    if not device_address:
        return False
    
    print(f"\n🔗 Connecting to {DEVICE_NAME} at {device_address}...")
    
    try:
        async with BleakClient(device_address) as client:
            print("✅ Connected successfully!")
            
            # First, discover all services and handles (abbreviated output)
            print("\n🔍 Validating GATT handles...")
            
            # Try to find characteristics by handle
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
            
            # Monitor for 5 minutes (300 seconds), sending commands every 15 seconds
            duration = 3600  # 1 hour
            interval = 15   # 15 seconds

            print(f"\n🚀 Starting 1-hour monitoring session...")
            print(f"📊 Sending command every {interval} seconds")
            print("=" * 60)
            
            start_time = asyncio.get_event_loop().time()
            next_command_time = start_time
            command_count = 0
            
            while True:
                current_time = asyncio.get_event_loop().time()
                
                # Check if 1 hour has elapsed
                if current_time - start_time >= duration:
                    print(f"\n⏰ 1-hour session completed!")
                    break
                
                # Check if it's time to send a command
                if current_time >= next_command_time:
                    command_count += 1
                    
                    # Reset response tracking for this command
                    response_count = 0
                    responses = []
                    
                    # Send the command
                    command_bytes = bytes.fromhex(COMMAND_PAYLOAD)
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    print(f"\n📤 Command #{command_count} at {timestamp}")
                    print(f"   Payload: {COMMAND_PAYLOAD}")
                    
                    await client.write_gatt_char(write_char, command_bytes)
                    
                    # Wait for responses
                    success = await wait_for_responses(expected_count=2, timeout=5)
                    
                    if success and len(responses) >= 2:
                        response1 = responses[0]
                        response2 = responses[1]
                        concatenated = response1 + response2
                        
                        print(f"   ✅ Received 2 responses:")
                        print(f"      Response 1: {response1}")
                        print(f"      Response 2: {response2}")
                        print(f"      Concatenated: {concatenated}")
                        
                        # Save to CSV data
                        csv_data.append({
                            'timestamp': timestamp,
                            'command': COMMAND_PAYLOAD,
                            'response1': response1,
                            'response2': response2,
                            'concatenated_response': concatenated
                        })
                        
                    else:
                        print(f"   ⚠️ Only received {len(responses)} response(s)")
                        # Still save incomplete data
                        csv_data.append({
                            'timestamp': timestamp,
                            'command': COMMAND_PAYLOAD,
                            'response1': responses[0] if len(responses) > 0 else '',
                            'response2': responses[1] if len(responses) > 1 else '',
                            'concatenated_response': ''.join(responses)
                        })
                    
                    # Schedule next command
                    next_command_time += interval
                
                # Sleep briefly to avoid busy waiting
                await asyncio.sleep(0.1)
            
            # Stop notifications
            await client.stop_notify(read_char)
            
            # Save data to CSV
            save_to_csv()
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        # Save any data we collected before the error
        if csv_data:
            save_to_csv()
        return False

async def main():
    print("🎯 Goal Zero Continuous Monitoring")
    print("=" * 50)
    print(f"Device: {DEVICE_NAME}")
    print(f"Write Handle: 0x{WRITE_HANDLE:04X}")
    print(f"Read Handle: 0x{READ_HANDLE:04X}")
    print(f"Command: {COMMAND_PAYLOAD}")
    print(f"Duration: 5 minutes")
    print(f"Interval: 15 seconds")
    print("=" * 50)
    
    success = await send_gatt_command()
    
    if success:
        print(f"\n📊 SESSION SUMMARY:")
        print(f"✅ Monitoring completed successfully")
        print(f"📥 Collected {len(csv_data)} command/response pairs")
        print(f"💾 Data saved to goalzero_responses.csv")
        
        # Show last few entries
        if csv_data:
            print(f"\n📋 Last entry:")
            last_entry = csv_data[-1]
            print(f"   Time: {last_entry['timestamp']}")
            print(f"   Concatenated Response: {last_entry['concatenated_response']}")
    else:
        print("\n❌ Monitoring session failed")
        if csv_data:
            print(f"💾 Partial data saved: {len(csv_data)} entries")

if __name__ == "__main__":
    asyncio.run(main())
