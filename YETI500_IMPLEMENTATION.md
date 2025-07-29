# Yeti 500 Implementation Summary

## Overview
Complete implementation of Goal Zero Yeti 500 device with comprehensive entity support, BLE communication, and user-configurable status polling as requested.

## Implementation Details

### Device Class: `Yeti500Device`
- **Location**: `custom_components/goalzero_ble/devices/yeti500.py`
- **Base Class**: `GoalZeroDevice`
- **Protocol**: JSON-RPC over BLE
- **Total Entities**: 44 (33 sensors, 3 switches, 5 numbers, 3 buttons)

### BLE Communication Pattern
- **Handle 0x0008**: Length prefix (4 bytes: 00:00:00:XX)
- **Handle 0x0003**: JSON data (fragmented for large messages)  
- **Handle 0x0005**: Status/acknowledgment
- **Message Format**: Length-prefixed JSON-RPC messages

### Entity Categories

#### Sensors (33 total)
**Battery Status (14 sensors)**:
- `battery_state_of_charge` - Battery State of Charge (%)
- `battery_remaining_wh` - Battery Remaining (Wh)
- `battery_voltage` - Battery Voltage (V)
- `battery_cycles` - Battery Cycles (cycles)
- `battery_temperature` - Battery Temperature (°C)
- `battery_time_to_empty_minutes` - Time to Empty (min)
- `battery_input_wh` - Battery Input Total (Wh)
- `battery_output_wh` - Battery Output Total (Wh)
- `battery_current_net` - Battery Current Net (A)
- `battery_current_net_avg` - Battery Current Net Average (A)
- `battery_power_net` - Battery Power Net (W)
- `battery_power_net_avg` - Battery Power Net Average (W)
- `battery_heater_relative_humidity` - Battery Heater RH (%)
- `battery_heater_temperature` - Battery Heater Temperature (°C)

**AC Output Port (4 sensors)**:
- `acOut_status` - AC Output Status
- `acOut_watts` - AC Output Power (W)
- `acOut_voltage` - AC Output Voltage (V)
- `acOut_amperage` - AC Output Current (A)

**AC Input Port (5 sensors)**:
- `acIn_status` - AC Input Status
- `acIn_watts` - AC Input Power (W)  
- `acIn_voltage` - AC Input Voltage (V)
- `acIn_amperage` - AC Input Current (A)
- `acIn_fast_charging` - AC Fast Charging

**12V Output Port (2 sensors)**:
- `v12Out_status` - 12V Output Status
- `v12Out_watts` - 12V Output Power (W)

**USB Output Port (2 sensors)**:
- `usbOut_status` - USB Output Status
- `usbOut_watts` - USB Output Power (W)

**Low Voltage DC Input Port (4 sensors)**:
- `lvDcIn_status` - LV DC Input Status
- `lvDcIn_watts` - LV DC Input Power (W)
- `lvDcIn_voltage` - LV DC Input Voltage (V)
- `lvDcIn_amperage` - LV DC Input Current (A)

**System Status (2 sensors)**:
- `wifi_rssi` - WiFi Signal Strength (dBm)
- `app_connected` - App Connected

#### Switches (3 total)
- `acOut_switch` - AC Output control
- `v12Out_switch` - 12V Output control  
- `usbOut_switch` - USB Output control

#### Numbers (5 total)
**Charge Profile Controls (3 numbers)**:
- `charge_profile_min_soc` - Charge Profile Min SOC (0-100%)
- `charge_profile_max_soc` - Charge Profile Max SOC (0-100%)
- `charge_profile_recharge_soc` - Charge Profile Recharge SOC (0-100%)

**Display Settings (2 numbers)**:
- `display_blackout_time` - Display Blackout Time (0-3600s)
- `display_brightness` - Display Brightness (0-100%)

#### Buttons (3 total)
- `reboot_device` - Reboot Device
- `reset_device` - Factory Reset
- `check_for_updates` - Check for Updates

### Key Features Implemented

#### 1. BLE Communication Patterns ✅
- JSON-RPC message structure with proper length prefixing
- Handle-based communication (0x0008 for length, 0x0003 for data, 0x0005 for status)
- Message fragmentation support for large payloads
- Proper error handling and timeout management

#### 2. User-Configurable Status Polling ✅
- Default 30-second update frequency
- `set_status_update_frequency(seconds)` method for user control
- Minimum 1-second frequency with validation
- Asynchronous status polling loop

#### 3. Comprehensive Data Reading ✅
On connection, reads all status types:
- Device information (`method: "device"`)
- Configuration settings (`method: "config"`)  
- Current status (`method: "status"`)
- Continuous status polling at user frequency

#### 4. Control Commands ✅
**Port Controls**:
- AC Output on/off via switch entity
- 12V Output on/off via switch entity
- USB Output on/off via switch entity

**Charge Profile Management**:
- Minimum SOC setting (0-100%)
- Maximum SOC setting (0-100%)
- Recharge SOC threshold (0-100%)

**Display Controls**:
- Blackout time configuration (0-3600 seconds)
- Brightness adjustment (0-100%)

**System Commands**:
- Device reboot
- Factory reset
- Firmware update check

#### 5. Data Parsing and Entity Integration ✅
- Parses battery status from JSON responses
- Extracts port data for all 5 port types
- Processes configuration settings
- Maps data to appropriate entity values
- Handles voltage scaling (AC input voltage correction)

### Method Overview

#### Core Methods
- `update_data(ble_manager)` - Main data update with all status reads
- `_send_json_message(message)` - BLE JSON communication
- `set_status_update_frequency(seconds)` - User polling control

#### Entity Definition Methods  
- `get_sensors()` - Returns 33 sensor definitions
- `get_switches()` - Returns 3 switch definitions
- `get_numbers()` - Returns 5 number entity definitions
- `get_buttons()` - Returns 3 button definitions

#### Control Methods
- `send_button_command(ble_manager, button_key)` - Button actions
- `set_switch_state(ble_manager, switch_key, state)` - Switch controls
- `set_number_value(ble_manager, number_key, value)` - Number settings

#### Internal Methods
- `_read_device_info()` - Device information request
- `_read_config()` - Configuration request  
- `_read_status()` - Status request
- `_control_port(port_name, state)` - Port control commands
- `_set_charge_profile(min_soc, max_soc, recharge_soc)` - Charge settings
- `_set_display_settings(blackout_time, brightness)` - Display settings
- `_reboot_device()` - System reboot
- `_factory_reset()` - Factory reset
- `_check_for_updates()` - Update check

### Protocol Implementation

#### Message Structure
```json
{
    "id": <message_id>,
    "method": "<command>",
    "params": {
        "action": "PATCH",
        "body": { /* command-specific data */ }
    }
}
```

#### Supported Methods
- `"device"` - Get device information
- `"config"` - Get/set configuration  
- `"status"` - Get/set status and controls
- `"lifetime"` - Get lifetime statistics
- `"ota"` - Get firmware update info

### Usage Example
```python
# Create device
device = Yeti500Device('AA:BB:CC:DD:EE:FF', 'My Yeti 500')

# Configure status polling (user request)
device.set_status_update_frequency(60)  # 60 seconds

# Update data (reads all status types)
data = await device.update_data(ble_manager)

# Control ports
await device.set_switch_state(ble_manager, 'acOut_switch', True)

# Set charge profile  
await device.set_number_value(ble_manager, 'charge_profile_max_soc', 85)

# System commands
await device.send_button_command(ble_manager, 'reboot_device')
```

## Request Fulfillment ✅

### Original Request Analysis
> "create a series of entities for both controls and statuses. Create the correct ble handle send and listen patterns and parse/concatenate the responses into their individual statuses. Make it as thorough as possible. On connect read all the other status requests, but allow the user to input a update frequency in seconds for looking at the Method:status."

### Fulfillment Status
1. **✅ Series of entities for controls and statuses**: 44 total entities covering all aspects
2. **✅ Correct BLE handle patterns**: Handles 0x0008, 0x0003, 0x0005 implemented 
3. **✅ Parse/concatenate responses**: JSON parsing with response concatenation
4. **✅ Thorough implementation**: 33 sensors, complete port coverage, all controls
5. **✅ Read all status on connect**: Device, config, status requests on connection
6. **✅ User-configurable update frequency**: `set_status_update_frequency()` method
7. **✅ Method:status polling**: Continuous status polling at user frequency

## Files Modified
1. `custom_components/goalzero_ble/devices/yeti500.py` - Complete device implementation
2. `yeti500_implementation_spec.json` - Generated specification document  
3. `extract_yeti_final.py` - Entity extraction script

## Next Steps
The Yeti 500 implementation is now complete and ready for integration with Home Assistant. The device class provides all requested functionality with comprehensive entity support and user-configurable status polling.
