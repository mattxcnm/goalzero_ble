#!/usr/bin/env python3
"""Test script to validate Alta 80 byte parsing logic."""

import sys
import os

# Add the custom component path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'goalzero_ble'))

from devices.alta80 import Alta80Device

def test_alta80_parsing():
    """Test the Alta 80 parsing with sample data."""
    
    # Create a test device
    device = Alta80Device("AA:BB:CC:DD:EE:FF", "gzf1-80-TEST")
    
    # Sample responses (you can replace these with actual responses from your device)
    # Each response should be 18 bytes, for a total of 36 bytes when concatenated
    test_responses = [
        "FEFE040001000000000000000000000000000000000000000000000000000000000000",  # 18 bytes
        "0000000000000000000000000000000000000000000000000000000000000000000000"   # 18 bytes
    ]
    
    print("🧪 Testing Alta 80 Status Parsing")
    print("=" * 50)
    
    # Parse the test data
    parsed_data = device._parse_status_responses(test_responses)
    
    print(f"✅ Parsed {len(parsed_data)} data points")
    print(f"📊 Response length: {parsed_data.get('response_length')} bytes")
    print(f"📝 Concatenated response: {parsed_data.get('concatenated_response')}")
    
    print("\n🔍 Decoded Values:")
    print(f"  Zone 1 Temperature (byte 18): {parsed_data.get('zone_1_temp')}°C")
    print(f"  Zone 1 Setpoint Exceeded (byte 34): {parsed_data.get('zone_1_setpoint_exceeded')}")
    print(f"  Zone 2 Temp High Res (byte 35): {parsed_data.get('zone_2_temp_high_res')}°C")
    print(f"  Compressor State A (byte 36): {parsed_data.get('compressor_state_a')}")
    print(f"  Compressor State B (byte 37): {parsed_data.get('compressor_state_b')}")
    
    print("\n📋 Sample Status Bytes (36 total):")
    for i in range(min(36, parsed_data.get('response_length', 0))):
        byte_val = parsed_data.get(f'status_byte_{i}')
        if byte_val is not None:
            print(f"  Byte {i:2d}: {byte_val:3d} (0x{byte_val:02X})")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_alta80_parsing()
