#!/usr/bin/env python3
"""
Comprehensive test for Alta 80 device implementation with rich entities and dynamic configuration.

Verifies:
1. Entity definition and exclusion of raw byte entities
2. Rich entity creation with meaningful names
3. Dynamic temperature unit detection
4. Dynamic slider limits from device data
5. Command generation for controls
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "custom_components"))

from goalzero_ble.devices.alta80 import Alta80
from homeassistant.const import UnitOfTemperature
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

def test_entity_exclusion():
    """Test that specified byte entities are excluded from sensors and numbers."""
    print("\n🔍 Testing Entity Exclusion...")
    
    device = Alta80()
    excluded_bytes = {0, 1, 6, 7, 8, 9, 10, 14, 15, 18, 26, 27, 35}
    
    # Check sensors
    sensors = device.get_sensors()
    excluded_sensor_keys = {f"byte_{b}_raw" for b in excluded_bytes}
    sensor_keys = {sensor["key"] for sensor in sensors}
    
    found_excluded = excluded_sensor_keys.intersection(sensor_keys)
    if found_excluded:
        print(f"❌ Found excluded sensor entities: {found_excluded}")
        return False
    else:
        print(f"✅ Successfully excluded {len(excluded_bytes)} byte sensors")
    
    # Check numbers
    numbers = device.get_numbers()
    excluded_number_keys = {f"byte_{b}_raw" for b in excluded_bytes}
    number_keys = {number["key"] for number in numbers}
    
    found_excluded = excluded_number_keys.intersection(number_keys)
    if found_excluded:
        print(f"❌ Found excluded number entities: {found_excluded}")
        return False
    else:
        print(f"✅ Successfully excluded {len(excluded_bytes)} byte numbers")
    
    return True

def test_rich_entities():
    """Test that rich entities are properly defined."""
    print("\n🔍 Testing Rich Entity Definitions...")
    
    device = Alta80()
    
    # Expected rich entities
    expected_sensors = {
        "eco_mode_status",
        "battery_protection_status", 
        "temperature_unit",
        "left_zone_temperature",
        "right_zone_temperature",
        "min_setpoint_temperature",
        "max_setpoint_temperature"
    }
    
    expected_numbers = {
        "zone1_setpoint",
        "zone2_setpoint"
    }
    
    expected_selects = {
        "battery_protection_level"
    }
    
    expected_switches = {
        "eco_mode"
    }
    
    # Check sensors
    sensors = device.get_sensors()
    sensor_keys = {sensor["key"] for sensor in sensors}
    missing_sensors = expected_sensors - sensor_keys
    if missing_sensors:
        print(f"❌ Missing sensor entities: {missing_sensors}")
        return False
    else:
        print(f"✅ All {len(expected_sensors)} rich sensor entities found")
    
    # Check numbers
    numbers = device.get_numbers()
    number_keys = {number["key"] for number in numbers}
    missing_numbers = expected_numbers - number_keys
    if missing_numbers:
        print(f"❌ Missing number entities: {missing_numbers}")
        return False
    else:
        print(f"✅ All {len(expected_numbers)} rich number entities found")
    
    # Check selects
    selects = device.get_selects()
    select_keys = {select["key"] for select in selects}
    missing_selects = expected_selects - select_keys
    if missing_selects:
        print(f"❌ Missing select entities: {missing_selects}")
        return False
    else:
        print(f"✅ All {len(expected_selects)} rich select entities found")
    
    # Check switches
    switches = device.get_switches()
    switch_keys = {switch["key"] for switch in switches}
    missing_switches = expected_switches - switch_keys
    if missing_switches:
        print(f"❌ Missing switch entities: {missing_switches}")
        return False
    else:
        print(f"✅ All {len(expected_switches)} rich switch entities found")
    
    return True

def test_dynamic_temperature_units():
    """Test dynamic temperature unit detection."""
    print("\n🔍 Testing Dynamic Temperature Unit Detection...")
    
    device = Alta80()
    
    # Test with Fahrenheit data (B14 = 0xFE)
    fahrenheit_data = bytearray(36)
    fahrenheit_data[14] = 0xFE
    fahrenheit_data[8] = 60   # Zone 1 setpoint
    fahrenheit_data[9] = 80   # Max temp  
    fahrenheit_data[10] = 40  # Min temp
    fahrenheit_data[18] = 72  # Left zone temp
    fahrenheit_data[35] = 68  # Right zone temp
    
    # Test parsing with Fahrenheit
    responses = [fahrenheit_data.hex().upper()]
    parsed_f = device._parse_status_responses(responses)
    
    if parsed_f.get("temperature_unit") != "°F":
        print(f"❌ Expected °F, got {parsed_f.get('temperature_unit')}")
        return False
    
    # Test with Celsius data (B14 = 0xFF)
    celsius_data = bytearray(36)
    celsius_data[14] = 0xFF
    celsius_data[8] = 15   # Zone 1 setpoint (°C)
    celsius_data[9] = 27   # Max temp (°C)
    celsius_data[10] = 4   # Min temp (°C) 
    celsius_data[18] = 22  # Left zone temp (°C)
    celsius_data[35] = 20  # Right zone temp (°C)
    
    # Test parsing with Celsius
    responses = [celsius_data.hex().upper()]
    parsed_c = device._parse_status_responses(responses)
    
    if parsed_c.get("temperature_unit") != "°C":
        print(f"❌ Expected °C, got {parsed_c.get('temperature_unit')}")
        return False
    
    print("✅ Temperature unit detection working for both °F and °C")
    
    # Test dynamic number configuration
    device._data = parsed_f  # Set Fahrenheit data
    f_config = device.get_dynamic_number_config("zone1_setpoint")
    
    if f_config["unit"] != UnitOfTemperature.FAHRENHEIT:
        print(f"❌ Expected Fahrenheit unit, got {f_config['unit']}")
        return False
    
    device._data = parsed_c  # Set Celsius data
    c_config = device.get_dynamic_number_config("zone1_setpoint")
    
    if c_config["unit"] != UnitOfTemperature.CELSIUS:
        print(f"❌ Expected Celsius unit, got {c_config['unit']}")
        return False
    
    print("✅ Dynamic number configuration working for temperature units")
    return True

def test_dynamic_slider_limits():
    """Test dynamic slider limits from device data."""
    print("\n🔍 Testing Dynamic Slider Limits...")
    
    device = Alta80()
    
    # Test data with specific min/max values
    test_data = bytearray(36)
    test_data[14] = 0xFE  # Fahrenheit
    test_data[8] = 65     # Zone 1 setpoint
    test_data[9] = 85     # Max temp
    test_data[10] = 45    # Min temp
    
    responses = [test_data.hex().upper()]
    parsed = device._parse_status_responses(responses)
    device._data = parsed
    
    config = device.get_dynamic_number_config("zone1_setpoint")
    
    if config["min_value"] != 45:
        print(f"❌ Expected min_value 45, got {config.get('min_value')}")
        return False
    
    if config["max_value"] != 85:
        print(f"❌ Expected max_value 85, got {config.get('max_value')}")
        return False
    
    print(f"✅ Dynamic slider limits working: {config['min_value']}°F to {config['max_value']}°F")
    
    # Test with Celsius data
    test_data[14] = 0xFF  # Celsius
    test_data[9] = 29     # Max temp (°C)
    test_data[10] = 7     # Min temp (°C)
    
    responses = [test_data.hex().upper()]
    parsed = device._parse_status_responses(responses)
    device._data = parsed
    
    config = device.get_dynamic_number_config("zone2_setpoint")
    
    if config["unit"] != UnitOfTemperature.CELSIUS:
        print(f"❌ Expected Celsius unit, got {config['unit']}")
        return False
    
    if config["min_value"] != 7:
        print(f"❌ Expected min_value 7, got {config.get('min_value')}")
        return False
    
    if config["max_value"] != 29:
        print(f"❌ Expected max_value 29, got {config.get('max_value')}")
        return False
    
    print(f"✅ Dynamic slider limits working in Celsius: {config['min_value']}°C to {config['max_value']}°C")
    return True

def test_command_generation():
    """Test command generation for control entities."""
    print("\n🔍 Testing Command Generation...")
    
    device = Alta80()
    
    # Test eco mode command
    eco_on = device._generate_eco_mode_command(True)
    eco_off = device._generate_eco_mode_command(False)
    
    if not eco_on or not eco_off:
        print("❌ Eco mode command generation failed")
        return False
    
    # Test battery protection command
    battery_cmd = device._generate_battery_protection_command("Medium")
    if not battery_cmd:
        print("❌ Battery protection command generation failed")
        return False
    
    # Test setpoint commands
    zone1_cmd = device._generate_zone1_setpoint_command(70.0)
    zone2_cmd = device._generate_zone2_setpoint_command(68.0)
    
    if not zone1_cmd or not zone2_cmd:
        print("❌ Setpoint command generation failed")
        return False
    
    # Test refresh command
    refresh_cmd = device._generate_refresh_command()
    if not refresh_cmd:
        print("❌ Refresh command generation failed")
        return False
    
    print("✅ All command generation methods working")
    return True

def test_data_parsing():
    """Test comprehensive data parsing with rich entities."""
    print("\n🔍 Testing Data Parsing...")
    
    device = Alta80()
    
    # Create comprehensive test data
    test_data = bytearray(36)
    test_data[0] = 0x01   # Should be excluded
    test_data[1] = 0x02   # Should be excluded  
    test_data[6] = 0x01   # Eco mode enabled
    test_data[7] = 0x02   # Battery protection medium
    test_data[8] = 70     # Zone 1 setpoint
    test_data[9] = 85     # Max temp
    test_data[10] = 45    # Min temp
    test_data[14] = 0xFE  # Fahrenheit
    test_data[15] = 0x03  # Should be excluded
    test_data[18] = 72    # Left zone temp
    test_data[26] = 0x04  # Should be excluded
    test_data[27] = 0x05  # Should be excluded
    test_data[35] = 68    # Right zone temp
    
    responses = [test_data.hex().upper()]
    parsed = device._parse_status_responses(responses)
    
    # Check rich entity values
    expected_values = {
        "eco_mode_status": "On",
        "battery_protection_status": "Medium", 
        "temperature_unit": "°F",
        "zone1_setpoint": 70,
        "max_setpoint_temperature": 85,
        "min_setpoint_temperature": 45,
        "left_zone_temperature": 72,
        "right_zone_temperature": 68
    }
    
    for key, expected in expected_values.items():
        actual = parsed.get(key)
        if actual != expected:
            print(f"❌ {key}: expected {expected}, got {actual}")
            return False
    
    # Check that excluded bytes are not in raw form
    excluded_keys = {"byte_0_raw", "byte_1_raw", "byte_6_raw", "byte_7_raw", 
                    "byte_8_raw", "byte_9_raw", "byte_10_raw", "byte_14_raw",
                    "byte_15_raw", "byte_18_raw", "byte_26_raw", "byte_27_raw", 
                    "byte_35_raw"}
    
    found_excluded = excluded_keys.intersection(parsed.keys())
    if found_excluded:
        print(f"❌ Found excluded raw bytes in parsed data: {found_excluded}")
        return False
    
    print("✅ Data parsing working correctly with rich entities")
    return True

def main():
    """Run comprehensive Alta 80 tests."""
    print("🧪 Alta 80 Comprehensive Implementation Test")
    print("=" * 50)
    
    tests = [
        test_entity_exclusion,
        test_rich_entities,
        test_dynamic_temperature_units,
        test_dynamic_slider_limits,
        test_command_generation,
        test_data_parsing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} FAILED")
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Alta 80 implementation is ready for use.")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
