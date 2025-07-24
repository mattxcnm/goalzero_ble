#!/usr/bin/env python3
"""Test setpoint parsing for Alta 80 device."""

import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_setpoint_parsing():
    """Test the setpoint parsing from Alta 80 device."""
    from goalzero_ble.devices.alta80 import Alta80Device
    
    # Create device instance
    device = Alta80Device("TestAlta80")
    
    # Test data: simulate a 36-byte response with known setpoint values
    # Byte 8 = Zone 1 setpoint, Byte 22 = Zone 2 setpoint
    test_responses = [
        # 36 bytes total: simulate realistic response
        "FEFE" +           # Bytes 0-1: Header (254, 254)
        "0000000000" +     # Bytes 2-6: Other data
        "2A" +             # Byte 7: Some value (42)
        "20" +             # Byte 8: Zone 1 setpoint = 32°F
        "0000000000" +     # Bytes 9-13: Other data
        "00000000" +       # Bytes 14-17: Other data
        "10" +             # Byte 18: Zone 1 temp = 16°C
        "000000" +         # Bytes 19-21: Other data
        "28" +             # Byte 22: Zone 2 setpoint = 40°F
        "000000000000" +   # Bytes 23-28: Other data
        "00000000" +       # Bytes 29-32: Other data
        "0000" +           # Bytes 33-34: Other data
        "0C"               # Byte 35: Zone 2 temp = 12°C
    ]
    
    print("Testing setpoint parsing with sample data:")
    print(f"Test response: {test_responses[0]}")
    print(f"Expected: Zone 1 setpoint = 32°F (byte 8), Zone 2 setpoint = 40°F (byte 22)")
    print()
    
    # Parse the response
    parsed_data = device._parse_status_responses(test_responses)
    
    # Check setpoint values
    zone1_setpoint = parsed_data.get("zone_1_setpoint")
    zone2_setpoint = parsed_data.get("zone_2_setpoint")
    
    print("Parsed results:")
    print(f"Zone 1 setpoint: {zone1_setpoint}°F")
    print(f"Zone 2 setpoint: {zone2_setpoint}°F")
    print()
    
    # Test negative setpoint values (signed integers)
    test_responses_negative = [
        # Same as above but with negative setpoints
        "FEFE" +           # Bytes 0-1: Header (254, 254)
        "0000000000" +     # Bytes 2-6: Other data
        "2A" +             # Byte 7: Some value (42)
        "E0" +             # Byte 8: Zone 1 setpoint = -32°F (224 as unsigned, -32 as signed)
        "0000000000" +     # Bytes 9-13: Other data
        "00000000" +       # Bytes 14-17: Other data
        "F0" +             # Byte 18: Zone 1 temp = -16°C
        "000000" +         # Bytes 19-21: Other data
        "D8" +             # Byte 22: Zone 2 setpoint = -40°F (216 as unsigned, -40 as signed)
        "000000000000" +   # Bytes 23-28: Other data
        "00000000" +       # Bytes 29-32: Other data
        "0000" +           # Bytes 33-34: Other data
        "F4"               # Byte 35: Zone 2 temp = -12°C
    ]
    
    print("Testing negative setpoint parsing:")
    print(f"Test response: {test_responses_negative[0]}")
    print(f"Expected: Zone 1 setpoint = -32°F (byte 8=0xE0), Zone 2 setpoint = -40°F (byte 22=0xD8)")
    print()
    
    # Parse the response
    parsed_data_negative = device._parse_status_responses(test_responses_negative)
    
    # Check setpoint values
    zone1_setpoint_neg = parsed_data_negative.get("zone_1_setpoint")
    zone2_setpoint_neg = parsed_data_negative.get("zone_2_setpoint")
    
    print("Parsed results:")
    print(f"Zone 1 setpoint: {zone1_setpoint_neg}°F")
    print(f"Zone 2 setpoint: {zone2_setpoint_neg}°F")
    print()
    
    # Verify parsing worked correctly
    success = True
    if zone1_setpoint != 32:
        print(f"❌ Zone 1 setpoint parsing failed: expected 32, got {zone1_setpoint}")
        success = False
    if zone2_setpoint != 40:
        print(f"❌ Zone 2 setpoint parsing failed: expected 40, got {zone2_setpoint}")
        success = False
    if zone1_setpoint_neg != -32:
        print(f"❌ Zone 1 negative setpoint parsing failed: expected -32, got {zone1_setpoint_neg}")
        success = False
    if zone2_setpoint_neg != -40:
        print(f"❌ Zone 2 negative setpoint parsing failed: expected -40, got {zone2_setpoint_neg}")
        success = False
    
    if success:
        print("✅ All setpoint parsing tests passed!")
    else:
        print("❌ Some setpoint parsing tests failed!")
    
    return success


if __name__ == "__main__":
    test_setpoint_parsing()
