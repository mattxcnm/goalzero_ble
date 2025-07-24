# Dynamic GATT Handle Discovery

## Problem
The Goal Zero Alta 80 device uses dynamic GATT handles that change on each connection. The original implementation used hardcoded handles (0x000A for write, 0x000C for read) which would fail when the device reassigned different handles.

## Solution
Implemented dynamic GATT characteristic discovery based on characteristic properties instead of hardcoded handle values.

## How It Works

### Characteristic Discovery by Properties

Instead of looking for specific handle values, the system now:

1. **Write Characteristic**: Looks for characteristics with `write` or `write-without-response` properties
2. **Notify Characteristic**: Looks for characteristics with `notify` or `indicate` properties

### Implementation Details

#### Alta 80 Device (`devices/alta80.py`)
```python
# Find characteristics dynamically by properties instead of hardcoded handles
write_char = None
read_char = None

for service in services.services.values():
    for char in service.characteristics:
        properties = char.properties
        
        # Look for write characteristic
        if not write_char and ('write' in properties or 'write-without-response' in properties):
            write_char = char
        
        # Look for read/notify characteristic  
        if not read_char and ('notify' in properties or 'indicate' in properties):
            read_char = char
```

#### BLE Manager (`ble_manager.py`)
Added helper methods:
- `_find_write_characteristic()`: Discovers write-capable characteristics
- `_find_notify_characteristic()`: Discovers notification-capable characteristics

### Handle Discovery Examples

Based on the error log, the available handles were:
- `0x0003, 0x0005, 0x0007, 0x000B, 0x000D`

The system will now:
1. Scan all available characteristics
2. Check their properties 
3. Select the first characteristic with appropriate properties
4. Log the selected handles for debugging

### Debugging Output

The system now provides detailed logging:
```
=== Alta 80 GATT Discovery ===
Service: 00001800-0000-1000-8000-00805f9b34fb
  Characteristic: 00002a00-0000-1000-8000-00805f9b34fb (Handle: 0x0003, Properties: ['read'])
  Characteristic: 00002a01-0000-1000-8000-00805f9b34fb (Handle: 0x0005, Properties: ['read'])
Service: 0000180a-0000-1000-8000-00805f9b34fb  
  Characteristic: 00002a29-0000-1000-8000-00805f9b34fb (Handle: 0x0007, Properties: ['read'])
Service: 6e400001-b5a3-f393-e0a9-e50e24dcca9e
  Characteristic: 6e400002-b5a3-f393-e0a9-e50e24dcca9e (Handle: 0x000B, Properties: ['write-without-response'])
  ✓ Selected write characteristic: 0x000B
  Characteristic: 6e400003-b5a3-f393-e0a9-e50e24dcca9e (Handle: 0x000D, Properties: ['notify'])
  ✓ Selected read/notify characteristic: 0x000D
=== End GATT Discovery ===
```

## Files Modified

### Core Implementation
- `devices/alta80.py`: Updated to use dynamic characteristic discovery
- `ble_manager.py`: Added dynamic discovery methods, removed hardcoded handle dependencies
- `coordinator.py`: Added GATT discovery tracking for debugging

### Testing Tools
- `diagnostic_tool.py`: Updated to use dynamic discovery
- `testing/goalzero_gatt_dynamic.py`: New test script with dynamic discovery

### Configuration
- `device_registry.py`: Removed hardcoded handle dependencies
- `const.py`: Kept handle constants for reference but no longer used in active code

## Benefits

1. **Robust Connection**: Works regardless of handle assignment
2. **Better Debugging**: Detailed logging of available characteristics
3. **Future Compatibility**: Will work with firmware updates that might change handle assignments
4. **Standard Compliance**: Uses BLE standard approach of discovering by properties

## Testing

Use the new dynamic test script:
```bash
python3 testing/goalzero_gatt_dynamic.py
```

Or the diagnostic tool:
```bash
python3 diagnostic_tool.py [device_address] [device_name]
```

Both will show the actual handles discovered and used for communication.

## Backward Compatibility

The hardcoded handle constants remain in `const.py` for reference, but the active code now uses dynamic discovery. This ensures the integration works with both old and new firmware versions of the Alta 80 device.
