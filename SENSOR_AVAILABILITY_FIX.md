# SENSOR AVAILABILITY FIX

## Problem Identified ✅

The debug logs showed that:
1. ✅ **Device communication is working perfectly**
2. ✅ **Data is being collected successfully** (43 sensor values)
3. ✅ **Parsing is working correctly** (Zone 1 temp: -1°C, Zone 2 temp: 3.4°C, etc.)
4. ❌ **Sensors showing "Unavailable"** despite successful data collection

## Root Cause

The issue was in the **sensor availability logic**:

```python
@property
def available(self) -> bool:
    return self.coordinator.last_update_success and self.coordinator.is_connected
```

For **Alta 80 devices**, the communication pattern is:
1. Connect to device
2. Get data via GATT 
3. **Disconnect immediately** 
4. Parse and store data

This means `is_connected` is always `False` after data collection, making all sensors "unavailable" even though data was successfully collected.

## Fix Applied

Modified the availability logic to handle the Alta 80's connect/disconnect pattern:

```python
@property
def available(self) -> bool:
    # For Alta 80 devices that connect/disconnect for each update,
    # availability is based only on last update success
    if self.coordinator.device_type == DEVICE_TYPE_ALTA80:
        return self.coordinator.last_update_success
    # For other devices that maintain persistent connections,
    # availability requires both successful update and active connection
    return self.coordinator.last_update_success and self.coordinator.is_connected
```

## Expected Result

After restarting Home Assistant:
- ✅ **All 43 sensors should become "Available"**
- ✅ **Sensor values should display actual data** instead of "Unknown"
- ✅ **Temperature sensors should show**: Zone 1: -1°C, Zone 2: 3.4°C
- ✅ **Status byte sensors should show**: Actual byte values (0-255)
- ✅ **Decoded sensors should show**: Compressor states, setpoint data, etc.

## Success Indicators

Look for:
- **Temperature values** in the sensor entities
- **Status byte values** (0-35) showing actual numbers  
- **"Available" status** instead of "Unavailable"
- **Regular updates** every 30 seconds

## Summary

The device has been working perfectly all along! The only issue was the sensor platform incorrectly marking entities as unavailable due to the Alta 80's connect/disconnect communication pattern.

Your logs show:
- Perfect BLE communication
- Correct characteristic selection (0x000B/0x000D)
- Successful data parsing (36 bytes total)
- All 43 sensor values being created

This fix should make all your sensors immediately available with real data!
