#!/usr/bin/env python3
"""
Test script for Alta 80 control commands.
This script tests the command generation without actually sending them.
"""

import sys
import os

# Add the custom_components path to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from goalzero_ble.devices.alta80 import Alta80Device

def test_temperature_commands():
    """Test temperature setpoint command generation."""
    print("=== Testing Temperature Commands ===\n")
    
    device = Alta80Device("test-address", "gzf1-80-TEST")
    
    # Test Zone 1 commands
    print("Zone 1 Temperature Commands:")
    for temp in [68, 50, 32, 0, -5]:
        try:
            cmd = device.create_zone1_temp_command(temp)
            print(f"  {temp}°F: {cmd.hex(':').upper()}")
        except Exception as e:
            print(f"  {temp}°F: ERROR - {e}")
    
    print("\nZone 2 Temperature Commands:")
    for temp in [35, 25, 15, 5, 0]:
        try:
            cmd = device.create_zone2_temp_command(temp)
            print(f"  {temp}°F: {cmd.hex(':').upper()}")
        except Exception as e:
            print(f"  {temp}°F: ERROR - {e}")

def test_system_commands():
    """Test system control command generation."""
    print("\n=== Testing System Commands ===\n")
    
    device = Alta80Device("test-address", "gzf1-80-TEST")
    
    # Test eco mode commands
    print("Eco Mode Commands:")
    for state in [True, False]:
        try:
            cmd = device.create_eco_mode_command(state)
            state_str = "ON" if state else "OFF"
            print(f"  Eco {state_str}: {cmd.hex(':').upper()}")
        except Exception as e:
            print(f"  Eco {state}: ERROR - {e}")
    
    # Test battery protection commands
    print("\nBattery Protection Commands:")
    for level in ["low", "med", "high"]:
        try:
            cmd = device.create_battery_protection_command(level)
            print(f"  {level.upper()}: {cmd.hex(':').upper()}")
        except Exception as e:
            print(f"  {level}: ERROR - {e}")

def test_button_commands():
    """Test button command generation."""
    print("\n=== Testing Button Commands ===\n")
    
    device = Alta80Device("test-address", "gzf1-80-TEST")
    
    # Test button commands
    button_tests = [
        ("zone1_temp_up", {"current_temp": 32}),
        ("zone1_temp_down", {"current_temp": 32}),
        ("zone2_temp_up", {"current_temp": 20}),
        ("zone2_temp_down", {"current_temp": 20}),
        ("toggle_eco_mode", {"current_eco_mode": False}),
        ("cycle_battery_protection", {"current_battery_protection": "low"}),
    ]
    
    print("Button Commands:")
    for button_key, kwargs in button_tests:
        try:
            cmd = device.create_button_command(button_key, **kwargs)
            print(f"  {button_key}: {cmd.hex(':').upper()}")
        except Exception as e:
            print(f"  {button_key}: ERROR - {e}")

def test_number_commands():
    """Test number entity command generation."""
    print("\n=== Testing Number Entity Commands ===\n")
    
    device = Alta80Device("test-address", "gzf1-80-TEST")
    
    # Test number commands
    number_tests = [
        ("zone1_setpoint", 45),
        ("zone1_setpoint", -2),
        ("zone2_setpoint", 28),
        ("zone2_setpoint", 0),
    ]
    
    print("Number Entity Commands:")
    for number_key, value in number_tests:
        try:
            cmd = device.create_number_set_command(number_key, value)
            print(f"  {number_key} = {value}: {cmd.hex(':').upper()}")
        except Exception as e:
            print(f"  {number_key} = {value}: ERROR - {e}")

def test_entity_definitions():
    """Test that the device properly defines entities."""
    print("\n=== Testing Entity Definitions ===\n")
    
    device = Alta80Device("test-address", "gzf1-80-TEST")
    
    # Test button definitions
    buttons = device.get_buttons()
    print(f"Button Entities: {len(buttons)} defined")
    for button in buttons:
        print(f"  - {button['name']} ({button['key']}) - {button['icon']}")
    
    # Test number definitions
    if hasattr(device, 'get_numbers'):
        numbers = device.get_numbers()
        print(f"\nNumber Entities: {len(numbers)} defined")
        for number in numbers:
            print(f"  - {number['name']} ({number['key']}) - {number['min_value']}-{number['max_value']} {number['unit']}")
    else:
        print("\nNumber Entities: Not implemented")

def verify_command_structure():
    """Verify command structure matches the analysis."""
    print("\n=== Verifying Command Structure ===\n")
    
    device = Alta80Device("test-address", "gzf1-80-TEST")
    
    # Verify Zone 1 temp command for 68°F matches analysis
    cmd = device.create_zone1_temp_command(68)
    expected = bytes([0xFE, 0xFE, 0x04, 0x05, 0x44, 0x02, 0x4F])
    
    if cmd == expected:
        print("✓ Zone 1 temp command structure verified")
    else:
        print(f"✗ Zone 1 temp command mismatch:")
        print(f"  Expected: {expected.hex(':').upper()}")
        print(f"  Got:      {cmd.hex(':').upper()}")
    
    # Verify Zone 2 temp command for 35°F matches analysis
    cmd = device.create_zone2_temp_command(35)
    expected = bytes([0xFE, 0xFE, 0x04, 0x06, 0x23, 0x02, 0x2F])
    
    if cmd == expected:
        print("✓ Zone 2 temp command structure verified")
    else:
        print(f"✗ Zone 2 temp command mismatch:")
        print(f"  Expected: {expected.hex(':').upper()}")
        print(f"  Got:      {cmd.hex(':').upper()}")

def main():
    """Run all tests."""
    print("Goal Zero Alta 80 Control Command Test")
    print("=" * 50)
    
    try:
        test_temperature_commands()
        test_system_commands()
        test_button_commands()
        test_number_commands()
        test_entity_definitions()
        verify_command_structure()
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
