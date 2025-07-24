# Goal Zero BLE Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/mattxcnm/goalzero_ble.svg)](https://github.com/mattxcnm/goalzero_ble/releases)
[![License](https://img.shields.io/github/license/mattxcnm/goalzero_ble.svg)](LICENSE)

A robust Home Assistant custom integration for Goal Zero devices via Bluetooth Low Energy (BLE). This integration provides comprehensive monitoring and control of Goal Zero devices with automatic discovery, detailed sensor data, and seamless Home Assistant integration.

## 🚀 Key Features

- **🔍 Automatic Discovery**: Automatically detects Goal Zero devices via Bluetooth
- **📱 Multiple Device Support**: Alta 80 fridge/freezer and Yeti 500 power station
- **📊 Comprehensive Sensors**: Detailed status monitoring with 35+ sensors for Alta 80
- **⚙️ Configurable Updates**: Customizable update intervals (10-300 seconds)
- **🔧 Modular Architecture**: Easily extensible for future Goal Zero devices
- **🏠 Full HA Integration**: Works seamlessly with automations, dashboards, and Lovelace cards
- **🔗 Connection Management**: Robust BLE connection handling with automatic recovery
- **📈 Lovelace Support**: Line graphs for numeric sensors, comprehensive device controls

## 📋 Supported Devices

| Device | Model Pattern | BLE Pattern | Sensors | Controls |
|--------|---------------|-------------|---------|----------|
| **Alta 80** | `gzf1-80-XXXXXX` | Goal Zero Fridge | 35+ detailed sensors | Temperature, Power, Eco mode |
| **Yeti 500** | `gzy5c-XXXXXXXXXXXX` | Goal Zero Power | Battery, Power, Voltage | Power controls |

### Alta 80 Detailed Sensors

The Alta 80 device provides extensive sensor data parsed from a 36-byte status message:

- **Core Sensors**: Battery %, Power consumption (W), Zone temperatures (°C)
- **Individual Bytes**: All 36 status bytes exposed as separate sensors
- **Temperature Data**: Signed integer decoding for accurate temperature readings
- **Status Indicators**: Setpoint exceeded, compressor states, various device flags
- **Lovelace Ready**: State classes for line graphs, proper units of measurement

## 🛠️ Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations" 
3. Click the three dots menu → "Custom repositories"
4. Add repository URL: `https://github.com/mattxcnm/goalzero_ble`
5. Category: "Integration"
6. Install "Goal Zero BLE"
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/mattxcnm/goalzero_ble/releases)
2. Extract and copy `custom_components/goalzero_ble/` to your Home Assistant config directory
3. Restart Home Assistant
4. Add the integration via Settings → Devices & Services

## ⚡ Setup & Configuration

### Automatic Discovery (Recommended)
1. **Power on** your Goal Zero device and ensure it's within Bluetooth range
2. Navigate to **Settings** → **Devices & Services** → **Add Integration**
3. The integration will **automatically discover** nearby Goal Zero devices
4. Click **Configure** when your device appears in the discovery list
5. **Set update interval** (10-300 seconds, recommended: 30-60s)
6. Click **Submit** to complete setup

### Manual Setup
If automatic discovery doesn't work:
1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Goal Zero BLE"
3. Enter your **exact device name** (case-sensitive, e.g., `gzf1-80-A1B2C3`)
4. Set **update interval** (10-300 seconds)
5. Click **Submit**

## 📊 Sensors & Controls

### Alta 80 Comprehensive Monitoring

**Primary Sensors:**
- Battery percentage
- Power consumption (W)
- Zone 1 & 2 temperatures (°C)
- Compressor status
- Setpoint exceeded indicators

**Detailed Status (35+ sensors):**
- Individual status bytes (0-35)
- Temperature data with signed integer handling
- Device state flags and indicators
- Full hex response for debugging

**Controls:**
- Temperature adjustment (up/down)
- Power on/off
- Eco mode toggle

### Yeti 500 Power Station

**Sensors:**
- Battery percentage
- Power output (W)
- Power input (W)
- Voltage (V)
- Current (A)

**Controls:**
- Power on/off

## 🏗️ Architecture & Technical Details

### Modular Design
The integration uses a sophisticated modular architecture designed for reliability and extensibility:

- **Device Registry**: Automatic device detection and type mapping via regex patterns
- **BLE Manager**: Robust Bluetooth connection management with retries and recovery
- **Dynamic GATT Discovery**: Characteristics discovered by properties, not hardcoded handles
- **Device Classes**: Modular device-specific parsing and command handling
- **Coordinator**: Data update lifecycle and connection state management
- **Error Handling**: Comprehensive error handling and diagnostic logging

### BLE Communication
- **Connection Management**: Automatic retries, stabilization delays, proper cleanup
- **GATT Discovery**: Dynamic characteristic discovery based on properties
- **Command System**: Device-specific hex payloads with retry logic
- **Response Parsing**: Custom parsing for each device type
- **Logging**: Extensive debug logging for troubleshooting

### Home Assistant Integration
- **Device Info**: Proper device registration without circular references
- **Entity Platform**: Dynamic sensor/button creation based on device capabilities
- **State Classes**: Measurement state classes for Lovelace line graphs
- **Availability**: Smart availability logic handling connect/disconnect patterns
- **Updates**: Configurable update intervals with coordinator pattern

## 🔍 Troubleshooting

### Device Not Found
- **Power Check**: Ensure Goal Zero device is powered on and active
- **Range**: Move device closer to Home Assistant server (BLE range ~10-30 feet)
- **Name Match**: For manual setup, device name must match exactly (case-sensitive)
- **Restart**: Try restarting the Goal Zero device and Home Assistant

### Connection Issues
- **Update Interval**: Reduce update frequency if experiencing disconnections (try 60+ seconds)
- **Interference**: Ensure no other apps/devices are connected to the Goal Zero device
- **Logs**: Check Home Assistant logs for specific BLE error messages
- **Bluetooth**: Restart Home Assistant's Bluetooth service if needed

### Sensor Values Unavailable
- **Device State**: Some sensors may not be available depending on device operational state
- **Communication**: Verify BLE communication is working in Home Assistant logs
- **Response Parsing**: Check logs for GATT response parsing errors
- **Recovery**: Integration will automatically retry failed commands and reconnect

### Common Error Messages
- **"Timeout waiting for connect response"**: Device out of range or busy
- **"GATT handle not found"**: GATT discovery may have failed, check logs
- **"No response from device"**: Device may be sleeping or disconnected
- **"AttributeError in sensor"**: Fixed in latest version, ensure you're updated

### Debug Logging
Enable debug logging to diagnose issues:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.goalzero_ble: debug
    bleak: debug
```

## 🔧 Advanced Configuration

### Custom Update Intervals
The integration supports per-device update intervals:
- **Alta 80**: Recommended 30-60 seconds (device handles frequent polling well)
- **Yeti 500**: Recommended 60-120 seconds (less frequent updates to preserve battery)
- **Range**: 10-300 seconds (configurable in integration setup)

### Lovelace Dashboard Examples

#### Alta 80 Temperature Card
```yaml
type: entities
title: Alta 80 Status
entities:
  - entity: sensor.gzf1_80_a1b2c3_zone_1_temperature
    name: Zone 1 Temp
  - entity: sensor.gzf1_80_a1b2c3_zone_2_temperature_high_res
    name: Zone 2 Temp
  - entity: sensor.gzf1_80_a1b2c3_battery_percentage
    name: Battery
  - entity: sensor.gzf1_80_a1b2c3_power_consumption
    name: Power Usage
```

#### Temperature History Graph
```yaml
type: history-graph
title: Temperature Trends
entities:
  - sensor.gzf1_80_a1b2c3_zone_1_temperature
  - sensor.gzf1_80_a1b2c3_zone_2_temperature_high_res
hours_to_show: 24
refresh_interval: 0
```

## 🚧 Development & Extension

### Adding New Devices
The integration is designed for easy extension. To add support for a new Goal Zero device:

1. **Device Registry** (`device_registry.py`):
   ```python
   DEVICE_PATTERNS = {
       r"new-device-pattern": {
           "device_class": "NewDevice",
           "model": "New Device Model",
           "manufacturer": "Goal Zero"
       }
   }
   ```

2. **Device Class** (`devices/new_device.py`):
   ```python
   class NewDevice(BaseDevice):
       def get_sensors(self):
           # Define device-specific sensors
       
       def parse_status_response(self, response):
           # Parse device response data
   ```

3. **GATT Configuration**: Add device-specific handles and commands

### Protocol Reverse Engineering
The integration includes tools for analyzing BLE communication:
- `testing/diagnostic_tool.py` - Device discovery and GATT analysis
- `testing/connection_test.py` - Connection stability testing
- `testing/goalzero_gatt_dynamic.py` - Dynamic GATT characteristic discovery

### Contributing
Pull requests welcome! Areas for contribution:
- Additional Goal Zero device support
- Enhanced sensor parsing and decoding
- Improved error handling and recovery
- Documentation and examples

## 📚 Technical Protocol Details

### BLE Communication Protocol
- **Discovery**: Uses Home Assistant's Bluetooth integration for device discovery
- **Connection**: Establishes GATT connection using Bleak library
- **Commands**: Sends hex payloads to device write characteristics
- **Responses**: Reads data from device notification/read characteristics
- **Parsing**: Device-specific interpretation of binary response data

### Alta 80 Protocol Specifics
- **Status Command**: `FEFE03010200` (6 bytes)
- **Response Length**: 36 bytes total (2 concatenated 18-byte responses)
- **Write Handle**: Discovered dynamically via GATT properties
- **Read Handle**: Discovered dynamically via GATT properties
- **Temperature Encoding**: Signed integers for temperature bytes (18, 35)
- **Static Bytes**: Bytes containing `0xFE` are filtered out as static

### Yeti 500 Protocol Specifics
- **Commands**: Device-specific hex payloads for power control
- **Status Parsing**: Battery, power, voltage, and current data extraction
- **Control Logic**: Power on/off command sequences

## ⚠️ Important Notes

### Disclaimer
This is an **unofficial integration** not affiliated with Goal Zero. The integration was developed through reverse engineering of BLE protocols and may not work with all firmware versions or device configurations. Use at your own risk.

### Device Compatibility
- **Firmware**: Integration tested with specific firmware versions - newer updates may change protocols
- **Models**: Limited to tested device models (Alta 80, Yeti 500) - other models may have different protocols
- **Region**: Device behavior may vary by region or configuration

### Privacy & Security
- **Local Communication**: All communication is local via Bluetooth - no cloud services involved
- **Data Handling**: Device data remains within your Home Assistant instance
- **No Authentication**: BLE communication uses Goal Zero's open protocol (no encryption)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Home Assistant community for the excellent BLE integration framework
- Bleak library developers for robust BLE communication tools
- Goal Zero device owners who contributed testing and feedback
- HACS for making custom integration distribution seamless

---

**Repository**: [https://github.com/mattxcnm/goalzero_ble](https://github.com/mattxcnm/goalzero_ble)  
**Issues**: [Report bugs or request features](https://github.com/mattxcnm/goalzero_ble/issues)  
**Discussions**: [Community support and questions](https://github.com/mattxcnm/goalzero_ble/discussions)
