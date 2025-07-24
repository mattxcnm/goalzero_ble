# Bug Fixes for Goal Zero BLE Integration

This document summarizes the fixes applied to address the reported issues.

## Issues Fixed

### 1. BLE Name Display in Integration Pop-up ✅

**Problem**: The integration pop-up wasn't showing the BLE name of the discovered device.

**Solution**: The config flow was already properly configured to show the device name, model, and address using description placeholders in `strings.json`. The `bluetooth_confirm` step displays:
- Device name (BLE name): `{name}`
- Device model: `{model}` 
- Device address: `{address}`

**Files modified**: 
- ✅ `strings.json` - Already properly configured
- ✅ `config_flow.py` - Already passing correct placeholders

### 2. Connection Timeout Errors ✅

**Problem**: "Timeout waiting for connect response while connecting to FD:06:22:F1:4D:2A after 10.0s, disconnect timed out: False, after 20.0s"

**Solutions**:
1. **Improved timeout handling**: Reduced BLE connect timeout from 15s to 12s to avoid the 10+2s pattern
2. **Better error logging**: Added specific timeout error handling with clear error types
3. **Enhanced connection cleanup**: Improved disconnect handling with proper error catching
4. **Alta 80 specific improvements**: Added connection timeout handling for the Alta 80's direct BLE communication

**Files modified**:
- ✅ `const.py` - Updated BLE timeout constants
- ✅ `ble_manager.py` - Enhanced connection handling and error reporting
- ✅ `devices/alta80.py` - Added timeout handling and better error messages

### 3. via_device Warning ✅

**Problem**: "Detected that custom integration 'goalzero_ble' calls `device_registry.async_get_or_create` referencing a non existing `via_device`"

**Solution**: Removed the circular `via_device` reference in `device_info`. The `via_device` was incorrectly set to the same identifier as the main device, creating a self-reference. For BLE devices, `via_device` should only be used when the device connects through another device (like a hub).

**Files modified**:
- ✅ `devices/base.py` - Removed `via_device` from device_info to prevent circular reference

### 4. GATT Handle Errors ✅

**Problem**: "Required GATT handles not found" - The device uses dynamic GATT handles that change on each connection, but the code was using hardcoded handle values (0x000A, 0x000C).

**Solutions**:
1. **Dynamic GATT Discovery**: Completely replaced hardcoded handle lookup with dynamic characteristic discovery based on properties
2. **Property-Based Selection**: Now searches for characteristics with `write`/`write-without-response` properties for writing and `notify`/`indicate` properties for notifications
3. **Enhanced Error Reporting**: When characteristics aren't found, logs all available handles and properties for debugging
4. **Robust Connection**: Works regardless of how the device assigns handle values

**Files modified**:
- ✅ `devices/alta80.py` - Replaced hardcoded handles (0x000A, 0x000C) with dynamic discovery
- ✅ `ble_manager.py` - Added `_find_write_characteristic()` and `_find_notify_characteristic()` methods
- ✅ `coordinator.py` - Added automatic GATT discovery on connection failures
- ✅ `diagnostic_tool.py` - Updated to use dynamic discovery
- ✅ `testing/goalzero_gatt_dynamic.py` - New test script demonstrating dynamic discovery

## Additional Improvements

### Enhanced Error Handling
- Added specific error types (TimeoutError, ConnectionError, etc.)
- Improved error messages with context about device state
- Better handling of partial responses from devices

### Debugging Tools
- Created `diagnostic_tool.py` for standalone BLE debugging
- Added comprehensive GATT service discovery logging
- Enhanced response validation and logging

### Connection Robustness
- Improved connection retry logic
- Better cleanup of failed connections
- More reliable disconnect handling

## Testing the Fixes

### 1. Test BLE Name Display
- Add a new Alta 80 device through Home Assistant
- Verify the integration setup shows the device name (e.g., "gzf1-80-F14D2A")

### 2. Test Connection Improvements
- Monitor logs for connection attempts
- Verify timeouts occur at 12s instead of 10s+
- Check that connection errors are more descriptive

### 3. Test via_device Fix
- Check Home Assistant logs for the via_device warning
- The warning should no longer appear

### 4. Test GATT Handle Discovery
- If GATT handle errors occur, check logs for detailed handle information
- Use the diagnostic tool: `python3 diagnostic_tool.py [device_address]`

## Files Modified

```
custom_components/goalzero_ble/
├── const.py                 # Updated BLE timeouts
├── ble_manager.py          # Enhanced connection handling and GATT discovery
├── coordinator.py          # Added automatic GATT discovery on failures  
├── devices/
│   ├── base.py            # Fixed via_device circular reference
│   └── alta80.py          # Improved timeout and error handling
├── config_flow.py         # Already configured correctly
└── strings.json           # Already configured correctly

diagnostic_tool.py          # New standalone debugging tool
```

## Usage

The integration should now:
1. Show proper device names in the setup flow
2. Handle connection timeouts more gracefully
3. Not generate via_device warnings
4. Provide detailed debugging information when GATT handles aren't found

If issues persist, use the diagnostic tool:
```bash
python3 diagnostic_tool.py [device_address] [device_name]
```

This will perform comprehensive BLE and GATT testing and provide detailed logs for further debugging.
