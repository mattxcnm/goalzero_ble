# TEMPERATURE AND LINE GRAPH IMPROVEMENTS

## Issues Addressed

### 1. History Card Line Graph Issue ✅
**Problem**: Byte entities showing as step graphs instead of smooth line graphs in Lovelace history cards.

**Solution**: Added `state_class: SensorStateClass.MEASUREMENT` to all numeric byte sensors.

### 2. Temperature Byte Decoding ✅
**Problem**: Bytes 18 and 35 are signed integers for Zone 1 and Zone 2 temperatures but were being treated as unsigned.

**Solution**: 
- Proper signed integer conversion for bytes 18 and 35
- Added dedicated `zone_2_temp` sensor for byte 35
- Both bytes now correctly handle negative temperatures

### 3. Unnecessary 0xFE Byte Sensors ✅
**Problem**: Creating sensors for bytes that always contain 0xFE and never change.

**Solution**: Filter out common 0xFE byte positions to reduce sensor clutter.

## Changes Made

### Sensor Definitions
```python
# Now skips 0xFE bytes: {0, 1, 13, 14, 19, 20, 25, 26}
# Adds state_class for line graphs
# Special handling for temperature bytes 18 and 35
```

### Temperature Parsing
```python
# Byte 18: Zone 1 Temperature (signed)
if zone_1_temp_raw > 127:
    zone_1_temp_raw = zone_1_temp_raw - 256

# Byte 35: Zone 2 Temperature (signed) 
if zone_2_temp_raw > 127:
    zone_2_temp_raw = zone_2_temp_raw - 256
```

### New Sensors Added
- **Zone 2 Temperature**: Direct signed integer from byte 35
- **Improved byte sensors**: With line graph support
- **Filtered sensors**: Only bytes that actually change

## Expected Results

After restarting Home Assistant:

### 1. Line Graphs ✅
- **History cards** will show smooth line graphs for all byte sensors
- **Better visualization** of data trends over time

### 2. Correct Temperature Readings ✅
- **Zone 1 Temperature** (byte 18): Correct signed values (can be negative)
- **Zone 2 Temperature** (byte 35): Correct signed values (can be negative)
- **Proper temperature units** (°C) and device classes

### 3. Cleaner Entity List ✅
- **Fewer unnecessary sensors** (0xFE bytes filtered out)
- **Only meaningful data** displayed
- **Easier to find relevant sensors**

## Customization

### Adjusting 0xFE Byte Filter
If you notice other bytes that always contain 0xFE, you can update this line:
```python
fe_bytes = {0, 1, 13, 14, 19, 20, 25, 26}  # Add/remove byte positions
```

### Temperature Scaling
If the temperature readings seem off, you can adjust the scaling in the parsing logic.

## Benefits

1. **Better History Visualization**: Smooth line graphs instead of step charts
2. **Accurate Temperature Data**: Proper signed integer handling for negative temps
3. **Cleaner Interface**: Fewer unnecessary sensors to manage
4. **Better Organization**: Clear temperature sensors with proper device classes

Your Goal Zero Alta 80 data should now be much more useful and visually appealing in Home Assistant! 📊🌡️
