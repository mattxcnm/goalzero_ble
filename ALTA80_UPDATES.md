# Goal Zero Alta 80 Integration Updates

This document describes the updates made to the Goal Zero BLE HACS integration based on the GATT communication patterns discovered in `goalzero_gatt.py`.

## Key Updates Made

### 1. Alta 80 Device Implementation (`devices/alta80.py`)

**Changes:**
- Updated to use direct GATT handle communication (0x000A write, 0x000C read)
- Implemented proper BLE command/response pattern with notifications
- Added `send_control_command()` method for button controls
- Enhanced data parsing with `_parse_gatt_responses()` method

**Key Features:**
- Direct BleakClient connection for reliable communication
- Handle-based characteristic discovery
- Response collection with timeout handling
- Structured data parsing for fridge-specific sensors

### 2. Constants (`const.py`)

**Added:**
- `ALTA80_WRITE_HANDLE = 0x000A` - Write characteristic handle
- `ALTA80_READ_HANDLE = 0x000C` - Read/notify characteristic handle  
- `ALTA80_COMMANDS` dictionary with device-specific commands
- Status request command: `"FEFE03010200"`

### 3. BLE Manager (`ble_manager.py`)

**Enhanced:**
- Added `send_command_with_handles()` method for GATT handle-based communication
- Support for multiple response collection
- Better error handling for handle discovery

### 4. Button Controls (`button.py`)

**Updated:**
- Added Alta 80 specific temperature and power control buttons
- Enhanced `GoalZeroTempButton` to support both legacy and GATT commands
- New button entities:
  - Temperature Up/Down (using GATT handles)
  - Power On/Off controls

### 5. GATT Discovery Utility (`gatt_discovery.py`)

**New Features:**
- Complete GATT service discovery utility
- Device name-based scanning
- Handle pair identification for write/read operations
- Communication testing functionality
- Service summary reporting

## Communication Protocol

Based on the `goalzero_gatt.py` testing:

### GATT Handles
- **Write Handle:** `0x000A` - For sending commands
- **Read Handle:** `0x000C` - For receiving notifications/responses

### Command Format
- **Status Request:** `FEFE03010200`
- **Temperature Control:** `FEFE0405xx02xxxx` (up/down variants)
- **Power Control:** `FEFE0501xxxxxxxx` (on/off variants)

### Response Pattern
- Devices typically send 2 responses per command
- Responses are hex-encoded data packets
- Notification-based communication with timeout handling

## Data Parsing

The Alta 80 device provides the following sensor data:

1. **Battery Percentage** - Extracted from response byte 3
2. **Fridge Temperature** - 16-bit little-endian from bytes 4-5 (divided by 10)
3. **Ambient Temperature** - 16-bit little-endian from bytes 6-7 (divided by 10)
4. **Power Consumption** - 16-bit little-endian from bytes 8-9
5. **Compressor Status** - Bit flags from byte 10

## Usage Examples

### Device Discovery
```python
from .gatt_discovery import discover_alta80_device
result = await discover_alta80_device("gzf1-80-F14D2A")
```

### Sending Commands
```python
# Via device method
success = await alta80_device.send_control_command("FEFE03010200")

# Via BLE manager
responses = await ble_manager.send_command_with_handles(
    "FEFE03010200", 0x000A, 0x000C, expected_responses=2
)
```

### Button Integration
The updated button platform automatically detects Alta 80 commands and uses the appropriate communication method (GATT handles vs. legacy UUIDs).

## Testing

Use the included `gatt_discovery.py` utility to:
1. Discover available Goal Zero devices
2. Map GATT services and characteristics
3. Test communication with different handle pairs
4. Verify command/response patterns

## Future Enhancements

1. **Protocol Validation** - Test with actual Alta 80 hardware to verify byte mappings
2. **Additional Commands** - Discover and implement remaining control commands
3. **Auto-Discovery** - Automatically detect device type and use appropriate handles
4. **Error Recovery** - Enhanced connection retry and error handling mechanisms

## Compatibility

These updates maintain backward compatibility with existing Goal Zero device implementations while adding enhanced Alta 80 support through the GATT handle-based communication discovered in the testing script.
