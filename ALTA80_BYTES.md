# Alta 80 Status Message Byte Mapping

This document describes the known byte positions in the Alta 80 status message response.

## Status Request Command

- **Command**: `FEFE03010200`
- **Expected Responses**: 2 (concatenated together)
- **Total Response Length**: Exactly 36 bytes (0-35)
- **Write Handle**: `0x000A`
- **Read Handle**: `0x000C`

## Known Byte Mappings

| Byte Position | Description | Data Type | Notes |
|---------------|-------------|-----------|-------|
| 18 | Zone 1 Temperature | Signed Integer | Temperature in Celsius |
| 34 | Zone 1 Setpoint Exceeded | Boolean | 0 = Not exceeded, 1 = Exceeded |
| 35 | Zone 2 Temperature (High Res) | Integer | High resolution temperature reading |

**Note**: Compressor state byte positions need to be determined from actual device analysis.

## Sensor Entities Created

### Individual Bytes (0-35)

- `status_byte_0` through `status_byte_35` - Raw byte values for all 36 bytes

### Decoded Values

- `zone_1_temp` - Zone 1 temperature in Celsius (from byte 18)
- `zone_1_setpoint_exceeded` - Boolean indicating setpoint exceeded (from byte 34)
- `zone_2_temp_high_res` - Zone 2 high resolution temperature (from byte 35)
- `compressor_state_a` - Compressor state A (byte position TBD)
- `compressor_state_b` - Compressor state B (byte position TBD)

### Metadata
- `concatenated_response` - Full hex response string
- `response_length` - Total bytes in response

## Usage in Home Assistant

After installation, the sensors will appear as:
- `sensor.{device_name}_zone_1_temperature`
- `sensor.{device_name}_zone_1_setpoint_exceeded`
- `sensor.{device_name}_zone_2_temperature_high_res`
- `sensor.{device_name}_compressor_state_a`
- `sensor.{device_name}_compressor_state_b`
- `sensor.{device_name}_status_byte_0` through `sensor.{device_name}_status_byte_19`
- `sensor.{device_name}_full_status_response`
- `sensor.{device_name}_response_length`

## Update Cycle

1. **Connect**: Establish BLE connection to device
2. **Request**: Send status command `FEFE03010200`
3. **Collect**: Wait for 2 response messages (up to 5 seconds)
4. **Parse**: Extract individual bytes and decode known values
5. **Update**: Update all sensor entities in Home Assistant
6. **Disconnect**: Close BLE connection
7. **Wait**: Sleep until next update interval

This connect/disconnect cycle ensures clean connections and follows the pattern established in the working `goalzero_gatt.py` script.

## Adding New Byte Mappings

To add new decoded byte values:

1. Update `get_sensors()` in `devices/alta80.py` to add new sensor definition
2. Update `_parse_status_responses()` to parse the specific byte position
3. Test with actual device to verify byte position and data interpretation

## Troubleshooting

- Check Home Assistant logs for connection and parsing errors
- Verify device is in range and powered on
- Increase update interval if seeing frequent connection failures
- Use the raw byte sensors to analyze unknown data patterns
