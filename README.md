# Goal Zero BLE Integration for Home Assistant

A Home Assistant HACS integration for Goal Zero BLE devices, providing wireless monitoring and control of portable power stations through Bluetooth Low Energy (BLE).

## 📋 Table of Contents

- [Features](#features)
- [Supported Devices](#supported-devices)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Sensors and Entities](#sensors-and-entities)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Development](#development)
- [Contributing](#contributing)

## ✨ Features

- **Automatic Device Discovery**: Detects Goal Zero devices via Bluetooth with automatic pattern matching
- **Robust BLE Communication**: Advanced connection handling with retries, timeouts, and error recovery
- **Rich Sensor Data**: Comprehensive monitoring of battery status, power flow, temperature, and device health
- **Modular Device Support**: Extensible architecture for adding new Goal Zero device models
- **User-Friendly Setup**: Simple configuration through Home Assistant's UI with device validation
- **Lovelace Integration**: Sensors include proper state classes for beautiful graphs and visualizations

## 🔌 Supported Devices

| Device | Model Pattern | Status | Notes |
|--------|---------------|--------|-------|
| **Alta 80** | `gzf1-80-XXXXXX` | ✅ Full Support | All 36 status bytes exposed, decoded key metrics |
| **Yeti 500** | `gzy5c-XXXXXXXXXXXX` | ⚠️ Partial Support | Basic framework ready, needs sensor mapping |

### Device Detection Patterns

- **Alta 80**: Devices with names matching `gzf1-80-[A-F0-9]{6}` (e.g., `gzf1-80-1A2B3C`)
- **Yeti 500**: Devices with names matching `gzy5c-[A-F0-9]{12}` (e.g., `gzy5c-1A2B3C4D5E6F`)

## 🚀 Quick Start

### Prerequisites

- Home Assistant with Bluetooth support
- HACS (Home Assistant Community Store) installed
- Goal Zero device in Bluetooth pairing mode

### 1. Install the Integration

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the menu (⋮) and select "Custom repositories"
4. Add this repository: `https://github.com/mattxcnm/goalzero_ble`
5. Set category to "Integration"
6. Click "Add"
7. Find "Goal Zero BLE" in HACS and install it
8. Restart Home Assistant

### 2. Add Your Device

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **"+ Add Integration"**
3. Search for **"Goal Zero BLE"**
4. Select your detected device OR enter the device name manually
5. Configure the update interval (default: 30 seconds)
6. Click **"Submit"**

Your Goal Zero device will appear in Home Assistant with all available sensors!

## 📦 Installation

### Option 1: HACS (Recommended)

1. **Add Custom Repository**:
   - HACS → Integrations → Menu (⋮) → Custom repositories
   - Repository: `https://github.com/mattxcnm/goalzero_ble`
   - Category: Integration
   - Add

2. **Install Integration**:
   - Search for "Goal Zero BLE" in HACS
   - Download and install
   - Restart Home Assistant

### Option 2: Manual Installation

1. **Download Files**:
   ```bash
   cd /config/custom_components/
   git clone https://github.com/mattxcnm/goalzero_ble.git
   ```

2. **Restart Home Assistant**

3. **Add Integration** via UI as described in Quick Start

## ⚙️ Configuration

### Basic Configuration

The integration is configured through Home Assistant's UI:

1. **Device Selection**: Choose from auto-discovered devices or enter manually
2. **Update Interval**: How often to poll the device (10-300 seconds, default: 30)
3. **Device Validation**: Automatic verification of device connectivity

### Configuration Options

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `update_interval` | 30 seconds | 10-300s | How often to poll device status |
| `device_name` | Auto-detected | - | BLE device name (manual entry) |

### Example Configuration Flow

```
┌─ Bluetooth Device Detected ─┐
│ Device: gzf1-80-A1B2C3      │
│ Model: Alta 80              │
│ Address: AA:BB:CC:DD:EE:FF  │
│                             │
│ Update Interval: [30] sec   │
│ [Cancel] [Submit]           │
└─────────────────────────────┘
```

## 📊 Sensors and Entities

### Alta 80 Sensors

The Alta 80 provides comprehensive monitoring through 36 status bytes:

#### 🔋 Power & Battery
- **Battery Level** (`sensor.alta80_battery_level`): Battery percentage (0-100%)
- **Power In** (`sensor.alta80_power_in`): Input power in watts
- **Power Out** (`sensor.alta80_power_out`): Output power in watts
- **Voltage** (`sensor.alta80_voltage`): Battery voltage in volts

#### 🌡️ Temperature
- **Internal Temperature** (`sensor.alta80_temp_internal`): Device internal temperature (°C)
- **External Temperature** (`sensor.alta80_temp_external`): External temperature sensor (°C)

#### 📈 Raw Data Sensors
- **Status Byte 0-35** (`sensor.alta80_byte_0` to `sensor.alta80_byte_35`): Raw status bytes for line graphs
  - State class: `measurement` (enables line graphs in Lovelace)
  - Filters out static `0xFE` bytes
  - Includes signed integer decoding for temperature bytes
- **Status Byte 0-35 Discrete** (`sensor.alta80_byte_0_discrete` to `sensor.alta80_byte_35_discrete`): Raw status bytes for discrete visualization
  - No state class (enables horizontal bar chart history)
  - Same data as line graph version but optimized for discrete value visualization
  - Ideal for history cards showing state changes over time

#### 🔘 Controls & Setpoints

**System Controls:**
- **Power** (`switch.alta80_power`): Turn device on/off
- **Eco Mode** (`switch.alta80_eco_mode`): Enable/disable eco mode
- **Battery Protection** (`select.alta80_battery_protection`): Set protection level (Low, Medium, High)

**Temperature Controls:**
- **Zone 1 Setpoint** (`number.alta80_zone1_setpoint`): Temperature slider control (-4°F to 68°F)
- **Zone 2 Setpoint** (`number.alta80_zone2_setpoint`): Temperature slider control (-4°F to 68°F)

**Data Refresh:**
- **Refresh Data** (`button.alta80_refresh`): Manually refresh device status

**Note**: Control state parsing (power, eco mode, battery protection) currently uses placeholder byte positions in the status response. These need to be refined through protocol analysis to accurately reflect actual device states.

### Entity Properties

All sensors include:
- **Device Info**: Manufacturer, model, firmware version, identifiers
- **State Classes**: Proper classification for Lovelace graphs and statistics
- **Units of Measurement**: Where applicable (%, W, V, °C)
- **Availability**: Based on last successful update, not persistent connection

### Lovelace Cards

Sensors support rich Lovelace visualizations:

```yaml
# Example: Power and control card
type: entities
title: Alta 80 Control
entities:
  - switch.alta80_power
  - switch.alta80_eco_mode
  - select.alta80_battery_protection
  - number.alta80_zone1_setpoint
  - number.alta80_zone2_setpoint

# Example: Sensor monitoring card  
type: entities
title: Alta 80 Monitoring
entities:
  - sensor.alta80_zone_1_temperature
  - sensor.alta80_zone_2_temperature
  - sensor.alta80_zone_1_setpoint
  - sensor.alta80_zone_2_setpoint

# Example: Historical graph
type: history-graph
title: Temperature History
entities:
  - sensor.alta80_zone_1_temperature
  - sensor.alta80_zone_2_temperature
hours_to_show: 24
```

## 🏗️ Architecture

### Component Overview

```
goalzero_ble/
├── __init__.py              # Integration setup and entry point
├── config_flow.py           # Configuration UI and device discovery
├── coordinator.py           # Data update coordination
├── ble_manager.py          # BLE connection and communication
├── device_registry.py      # Device type detection and registry
├── sensor.py               # Sensor platform implementation
├── button.py               # Button platform implementation
├── const.py                # Constants and configuration
├── manifest.json           # Integration metadata
├── strings.json            # UI text and translations
└── devices/                # Device-specific implementations
    ├── __init__.py
    ├── base.py             # Base device class
    ├── alta80.py           # Alta 80 specific implementation
    └── yeti500.py          # Yeti 500 specific implementation
```

### Key Components

#### 1. **BLE Manager** (`ble_manager.py`)
- Handles all Bluetooth Low Energy communication
- Dynamic GATT service and characteristic discovery
- Connection retries, timeouts, and stabilization
- Command queuing and response handling

#### 2. **Device Registry** (`device_registry.py`)
- Pattern-based device type detection
- Device-specific configuration and capabilities
- Extensible for new device models

#### 3. **Coordinator** (`coordinator.py`)
- Manages data updates and caching
- Error handling and recovery
- Entity availability management

#### 4. **Device Classes** (`devices/`)
- **Base Device**: Common functionality and interfaces
- **Alta 80**: Full implementation with 36-byte status parsing
- **Yeti 500**: Framework ready for implementation

### BLE Communication Flow

```
[Home Assistant] 
       ↓
[Coordinator] ← Timer → [Update Interval]
       ↓
[BLE Manager] → [Device Discovery] → [GATT Services]
       ↓
[Device Class] → [Data Parsing] → [Sensor Updates]
       ↓
[Sensor Platform] → [Entity Updates] → [UI Display]
```

### Connection Management

- **Dynamic Discovery**: All GATT services and characteristics discovered at runtime
- **Retry Logic**: Configurable retries with exponential backoff
- **Timeout Handling**: Separate timeouts for connection, discovery, and operations
- **Stabilization**: Delays after connection for device stability
- **Error Recovery**: Graceful handling of BLE disconnections and failures

## 🔧 Troubleshooting

### Common Issues

#### 1. **Device Not Found**
```
Error: Device not found via Bluetooth
```
**Solutions**:
- Ensure device is in pairing/discoverable mode
- Check device is within Bluetooth range
- Verify device name matches supported patterns
- Restart Bluetooth service: Settings → System → Hardware

#### 2. **Connection Timeouts**
```
Error: Cannot connect to device
```
**Solutions**:
- Move closer to the device
- Check for Bluetooth interference
- Restart the Goal Zero device
- Increase update interval to reduce connection frequency

#### 3. **Sensor Data Not Updating**
**Check**:
- Device connectivity in Bluetooth settings
- Integration logs for connection errors
- Update interval configuration
- Device battery level

#### 4. **Missing Sensors**
**For Alta 80**: All 36 bytes + decoded sensors should appear
**Solutions**:
- Reload the integration
- Check logs for parsing errors
- Verify device firmware compatibility

### Debug Logging

Enable detailed logging for troubleshooting:

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.goalzero_ble: debug
    custom_components.goalzero_ble.ble_manager: debug
    custom_components.goalzero_ble.devices.alta80: debug
```

### Log Analysis

Common log patterns:
- `✓ Connected to device` - Successful connection
- `✓ Discovered GATT services` - Service discovery complete
- `✓ Status update successful` - Data retrieved successfully
- `⚠ Connection retry` - Temporary connection issues
- `✗ Failed to connect` - Persistent connection problems

### Device-Specific Issues

#### Alta 80
- **Status byte filtering**: Bytes with value `0xFE` are filtered out as static
- **Temperature decoding**: Bytes 18 and 35 use signed integer interpretation
- **Connection stability**: May require 2-3 second stabilization after connection

#### Yeti 500
- **Limited implementation**: Framework present, needs sensor mapping
- **Protocol differences**: May use different BLE command structure

### Performance Optimization

#### Update Intervals
- **Frequent updates (10-20s)**: Real-time monitoring, higher battery drain
- **Standard updates (30-60s)**: Balanced monitoring and efficiency  
- **Conservation mode (120-300s)**: Minimal impact, slower updates

#### Connection Efficiency
- Avoid simultaneous BLE connections from multiple apps
- Use longer intervals if experiencing frequent disconnections
- Consider device placement for optimal Bluetooth signal

## 🔬 Advanced Usage

### Custom Sensor Creation

Create additional sensors from raw status bytes:

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Alta 80 Power Balance"
        state: >
          {{ (states('sensor.alta80_power_in') | float) - 
             (states('sensor.alta80_power_out') | float) }}
        unit_of_measurement: "W"
        device_class: power
```

### Automation Examples

#### Low Battery Alert
```yaml
automation:
  - alias: "Alta 80 Low Battery"
    trigger:
      - platform: numeric_state
        entity_id: sensor.alta80_battery_level
        below: 20
    action:
      - service: notify.mobile_app
        data:
          message: "Alta 80 battery level is {{ states('sensor.alta80_battery_level') }}%"
```

#### Power Monitoring
```yaml
automation:
  - alias: "Alta 80 High Power Draw"
    trigger:
      - platform: numeric_state
        entity_id: sensor.alta80_power_out
        above: 50
        for: "00:05:00"
    action:
      - service: notify.home_assistant
        data:
          message: "Alta 80 has been drawing {{ states('sensor.alta80_power_out') }}W for 5 minutes"
```

### API Access

Access device data programmatically:

```python
# Example: Get current status
hass = get_hass()
coordinator = hass.data[DOMAIN]["YOUR_DEVICE_ID"]
device_data = coordinator.data

# Access specific values
battery_level = device_data.get("battery_level")
power_out = device_data.get("power_out")
```

### Integration with Other Systems

#### MQTT Bridge
```yaml
# Publish to MQTT
automation:
  - alias: "Publish Alta 80 to MQTT"
    trigger:
      - platform: state
        entity_id: sensor.alta80_battery_level
    action:
      - service: mqtt.publish
        data:
          topic: "goalzero/alta80/battery"
          payload: "{{ states('sensor.alta80_battery_level') }}"
```

#### InfluxDB Export
```yaml
# configuration.yaml
influxdb:
  include:
    entities:
      - sensor.alta80_battery_level
      - sensor.alta80_power_in
      - sensor.alta80_power_out
      - sensor.alta80_voltage
```

## 💻 Development

### Development Environment Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/mattxcnm/goalzero_ble.git
   cd goalzero_ble
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Code Structure

#### Adding New Device Support

1. **Create Device Class** (`devices/new_device.py`):
   ```python
   from .base import BaseGoalZeroDevice
   
   class NewDevice(BaseGoalZeroDevice):
       def parse_status_data(self, data: bytes) -> dict[str, Any]:
           # Implement device-specific parsing
           pass
   ```

2. **Register Device** (`device_registry.py`):
   ```python
   _DEVICE_PATTERNS = {
       # Add pattern for new device
       "new_device": re.compile(r"^pattern-regex$"),
   }
   
   _DEVICE_CLASSES = {
       # Map to device class
       "new_device": NewDevice,
   }
   ```

3. **Update Constants** (`const.py`):
   ```python
   DEVICE_TYPE_NEW = "new_device"
   NEW_DEVICE_MODEL = "New Device Model"
   ```

#### Testing

Run diagnostic tools:

```bash
# Test BLE connection and discovery
python diagnostic_tool.py

# Test data parsing
python test_parsing.py

# Test specific connection issues
python connection_test.py
```

### Debugging Tools

The repository includes several diagnostic scripts:

#### `diagnostic_tool.py`
- Comprehensive BLE scanning and testing
- GATT service discovery and characteristic testing
- Connection stability analysis

#### `test_parsing.py`
- Parse and analyze status data
- Test sensor value extraction
- Verify data interpretation

#### `connection_test.py`
- Test basic BLE connectivity
- Verify device accessibility
- Debug connection issues

### Code Quality

The project follows Home Assistant development standards:

- **Type Hints**: Full type annotation
- **Logging**: Comprehensive debug and error logging
- **Error Handling**: Graceful failure recovery
- **Documentation**: Inline comments and docstrings
- **Testing**: Unit tests and integration tests

### Contributing Guidelines

1. **Fork and Clone**: Create your own fork of the repository
2. **Create Branch**: Use descriptive branch names (`feature/yeti-500-support`)
3. **Code Standards**: Follow existing code style and patterns
4. **Test Changes**: Verify with real devices when possible
5. **Documentation**: Update README and inline documentation
6. **Pull Request**: Submit with clear description of changes

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Areas for Contribution

1. **Device Support**: 
   - Yeti 500 sensor mapping and testing
   - Additional Goal Zero device models
   - Enhanced device-specific features

2. **Features**:
   - Device control commands (where supported)
   - Enhanced error recovery
   - Performance optimizations
   - Additional sensor calculations

3. **Documentation**:
   - Device-specific setup guides
   - Troubleshooting scenarios
   - Lovelace card examples
   - Video tutorials

4. **Testing**:
   - Real device testing across different firmware versions
   - Edge case scenario testing
   - Performance benchmarking
   - Automated testing framework

### Development Process

1. **Open an Issue**: Discuss your idea or bug report
2. **Fork Repository**: Create your development environment
3. **Implement Changes**: Follow coding standards and test thoroughly
4. **Submit Pull Request**: Include tests and documentation updates
5. **Code Review**: Collaborate on refinements
6. **Merge**: Integration into main branch

### Code of Conduct

- Be respectful and constructive in all interactions
- Focus on technical merit and user benefit
- Help newcomers and answer questions
- Report bugs and suggest improvements
- Test changes with real hardware when possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## � Status Response Protocol Details

### Alta 80 Status Response Breakdown

The Alta 80 device provides comprehensive status information through a 36-byte response that contains detailed sensor data and device state information. This section documents the current understanding of each byte position.

#### Communication Protocol

**Status Request Command**: `FEFE03010200` (6 bytes)  
**Response Format**: Two 18-byte notifications (concatenated to 36 bytes total)  
**GATT Handles**: Dynamically discovered via service properties

- Write Handle: Characteristic with `write-without-response` property
- Read Handle: Characteristic with `notify` or `indicate` property

#### 36-Byte Status Response Structure

| Byte | Hex Range | Data Type | Description | Current Understanding | Unit |
|------|-----------|-----------|-------------|---------------------|------|
| 0 | 0x00 | Static | Header/Protocol | Always `0xFE` (254) | - |
| 1 | 0x01 | Static | Header/Protocol | Always `0xFE` (254) | - |
| 2 | 0x02 | Unknown | Protocol/Status | Variable data | - |
| 3 | 0x03 | Unknown | System Status | Variable data | - |
| 4 | 0x04 | Unknown | Device State | Variable data, may contain power state | - |
| 5 | 0x05 | Unknown | System Flag | Variable data, may contain eco mode flag | - |
| 6 | 0x06 | Unknown | Control State | Variable data, may contain battery protection level | - |
| 7 | 0x07 | Unknown | System Data | Variable data | - |
| **8** | **0x08** | **Signed Int** | **Zone 1 Setpoint** | **Temperature setpoint in °F** | **°F** |
| 9 | 0x09 | Unknown | System Data | Variable data | - |
| 10 | 0x0A | Unknown | System Data | Variable data | - |
| 11 | 0x0B | Unknown | System Data | Variable data | - |
| 12 | 0x0C | Unknown | System Data | Variable data | - |
| 13 | 0x0D | Static | Protocol | Often `0xFE` (254) | - |
| 14 | 0x0E | Static | Protocol | Often `0xFE` (254) | - |
| 15 | 0x0F | Unknown | System Data | Variable data | - |
| 16 | 0x10 | Unknown | System Data | Variable data | - |
| 17 | 0x11 | Unknown | System Data | Variable data | - |
| **18** | **0x12** | **Signed Int** | **Zone 1 Temperature** | **Current temperature in °C** | **°C** |
| 19 | 0x13 | Static | Protocol | Often `0xFE` (254) | - |
| 20 | 0x14 | Static | Protocol | Often `0xFE` (254) | - |
| 21 | 0x15 | Unknown | System Data | Variable data | - |
| **22** | **0x16** | **Signed Int** | **Zone 2 Setpoint** | **Temperature setpoint in °F** | **°F** |
| 23 | 0x17 | Unknown | System Data | Variable data | - |
| 24 | 0x18 | Unknown | System Data | Variable data | - |
| 25 | 0x19 | Static | Protocol | Often `0xFE` (254) | - |
| 26 | 0x1A | Static | Protocol | Often `0xFE` (254) | - |
| 27 | 0x1B | Unknown | System Data | Variable data | - |
| 28 | 0x1C | Unknown | System Data | Variable data | - |
| 29 | 0x1D | Unknown | System Data | Variable data | - |
| 30 | 0x1E | Unknown | System Data | Variable data | - |
| 31 | 0x1F | Unknown | System Data | Variable data | - |
| 32 | 0x20 | Unknown | System Data | Variable data | - |
| 33 | 0x21 | Unknown | System Data | Variable data | - |
| **34** | **0x22** | **Boolean** | **Zone 1 Setpoint Exceeded** | **Temperature limit exceeded flag** | **-** |
| **35** | **0x23** | **Signed Int** | **Zone 2 Temperature** | **Current temperature in °C** | **°C** |

#### Known Decoded Values

The integration automatically decodes several key values from the raw bytes:

##### Temperature Data

- **Zone 1 Temperature (Byte 18)**: Signed integer representing current temperature in Celsius
- **Zone 2 Temperature (Byte 35)**: Signed integer representing current temperature in Celsius  
- **Zone 1 Setpoint (Byte 8)**: Signed integer representing target temperature in Fahrenheit (-4°F to 68°F)
- **Zone 2 Setpoint (Byte 22)**: Signed integer representing target temperature in Fahrenheit (-4°F to 68°F)

##### Status Indicators

- **Zone 1 Setpoint Exceeded (Byte 34)**: Boolean flag indicating if Zone 1 temperature has exceeded setpoint
- **Zone 2 High-Res Temperature**: Calculated as `Byte 35 / 10.0` for higher precision

##### Control State Values (Under Research)

The integration attempts to extract current control states from the status response:

- **Power State (Byte 4)**: Currently uses non-zero value to indicate power on (needs verification)
- **Eco Mode (Byte 5)**: Currently checks lowest bit for eco mode status (needs verification)  
- **Battery Protection (Byte 6)**: Currently maps values 0-1→Low, 2→Medium, 3+→High (needs verification)

**Note**: These control state interpretations are preliminary and may need adjustment based on actual device behavior and protocol analysis.

##### Static Bytes (Filtered)

The following bytes typically contain static values (`0xFE` = 254) and are filtered from sensor display:

- Bytes 0, 1: Protocol header
- Bytes 13, 14: Protocol markers  
- Bytes 19, 20: Protocol markers
- Bytes 25, 26: Protocol markers

#### Signed Integer Interpretation

Temperature-related bytes (8, 18, 22, 35) use signed 8-bit integer encoding:

```python
# Convert unsigned byte to signed integer
if byte_value > 127:
    signed_value = byte_value - 256
else:
    signed_value = byte_value
```

#### Control Commands

The device accepts various control commands that modify setpoint values:

##### Temperature Setpoint Commands

- **Zone 1 Temp**: `FEFE04053502B7` (example for 53°F)
- **Zone 2 Temp**: `FEFE04062802AC` (example for 40°F)
- **Command Structure**: `FEFE 04 05/06 TEMP 02 CHECKSUM`

##### System Control Commands

- **Eco Mode Toggle**: `FEFE21...` (complex 20-byte command)
- **Battery Protection**: `FEFE21...` (complex 20-byte command with level bytes)

#### Research Status

🟢 **Fully Decoded**: Bytes 8, 18, 22, 34, 35  
🟡 **Partially Understood**: Bytes 0, 1, 13, 14, 19, 20, 25, 26 (static markers)  
� **Control States (Under Research)**: Bytes 4, 5, 6 (power, eco mode, battery protection - preliminary interpretation)  
�🔴 **Unknown**: Bytes 2-3, 7, 9-12, 15-17, 21, 23-24, 27-33  

#### Future Research Areas

1. **Control State Mapping**: Identifying exact bytes for power state, eco mode, and battery protection levels
2. **Power Monitoring**: Locating bytes related to power consumption and battery status  
3. **Compressor State**: Locating compressor operation indicators in remaining bytes
4. **System Flags**: Understanding device mode and status indicators
5. **Error Codes**: Identifying fault and diagnostic information

#### Protocol Analysis Tools

The repository includes a diagnostic script to help identify control state bytes:

```bash
# Run control state analyzer
python analyze_control_states.py
```

**Usage**:
1. Run the script and capture baseline status
2. Change one control setting on the device (power, eco mode, or battery protection)  
3. Capture status again to see which bytes changed
4. Repeat for each control to map specific bytes to control states

This analysis helps refine the control state parsing logic in the integration.

This status response analysis is ongoing, and contributions from the community help improve the understanding of the protocol. If you have insights into any of the unknown bytes, please [contribute to the project](https://github.com/mattxcnm/goalzero_ble/issues).

## �🙏 Acknowledgments

- **Home Assistant Community**: For the excellent platform and development tools
- **Goal Zero**: For creating innovative portable power solutions
- **HACS**: For simplifying custom integration distribution
- **Bleak**: For robust Python BLE communication capabilities
- **Contributors**: Everyone who has tested, reported issues, and contributed code

---

**⭐ If this integration helps you monitor your Goal Zero devices, please give it a star!**

For support, feature requests, or bug reports, please [open an issue](https://github.com/mattxcnm/goalzero_ble/issues) on GitHub.
