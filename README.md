# Goal Zero BLE Integration for Home Assistant

A Home Assistant HACS integration for Goal Zero BLE devices, providing wireless monitoring and control of portable power stations through Bluetooth Low Energy (BLE).

> [!WARNING]
> This Integration is incomplete and in active development. Please report all bugs, glitches, and suggestions under "Issues".

> [!IMPORTANT]
> Review Legal Disclaimer prior to use of this integration.


## 📋 Table of Contents

- [Features](#-features)
- [Supported Devices](#-supported-devices)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Sensors and Entities](#-sensors-and-entities)
- [Architecture](#-architecture)
- [Development](#-development)
- [Contributing](#-contributing)
- [Legal Disclaimer](#-legal-disclaimer)

## ✨ Features

- **Automatic Device Discovery**: Detects Goal Zero devices via Bluetooth with automatic pattern matching
- **Robust BLE Communication**: Advanced connection handling with retries, timeouts, and error recovery
- **Rich Sensor Data**: Comprehensive monitoring of device states and sensors
- **Modular Device Support**: Extensible architecture for adding new Goal Zero device models
- **Quick Setup**: Simple configuration through Home Assistant's UI with device validation


## 🔌 Supported Devices

| Device | Model Pattern | Status | Notes |
|--------|---------------|--------|-------|
| **Alta 80** | `gzf1-80-XXXXXX` | ⚠️ Partial Support | All 36 status bytes exposed, decoded basic metrics |
| **Yeti 500** | `gzy5c-XXXXXXXXXXXX` | 🚧 Pending Development | Basic framework ready, needs device testing |

### Device Detection Patterns

- **Alta 80**: Devices with names matching `gzf1-80-[A-F0-9]{6}` (e.g., `gzf1-80-1A2B3C`)
- **Yeti 500**: Devices with names matching `gzy5c-[A-F0-9]{12}` (e.g., `gzy5c-1A2B3C4D5E6F`)


## 📦 Installation

### Prerequisites

- Home Assistant with Bluetooth support
- HACS (Home Assistant Community Store) installed
- Goal Zero device
  - Alta 80: Ready out-of-the-box and powered-on.
  - Yeti 500: Needs BLE enabled

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

No instructions will be provided here. Only complete the manual installation if you are familiar with custom integrations in Home Assistant.

## ⚙️ Configuration

The integration is configured through Home Assistant's UI:

1. **Add New Device**:
   1. Choose from auto-discovered
   2. Enter manually from Setting > Devices and services > ADD INTEGRATION > Goal Zero BLE
2. **Update Interval**: How often to poll the device (10-300 seconds, default: 30)

### Configuration Options

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `update_interval` | 30 seconds | 10-300s | How often to poll device status |
| `device_name` | Auto-detected | - | BLE device name (manual entry) |


## 📊 Sensors and Entities

### Alta 80 Sensors

The Alta 80 provides comprehensive monitoring through 36 status bytes over BLE GATT:

#### 🌡️ Temperature

- Zone 1 & 2 set point temperature
- Zone 1 & 2 actual temperature

#### 📈 Raw Data Sensors

- **Status Byte 0-35** (`sensor.alta80_byte_0` to `sensor.alta80_byte_35`): Raw status bytes for line graphs
  - State class: `measurement` (enables line graphs in Lovelace)
  - Filters out static `0xFE` bytes
  - Includes signed integer decoding for temperature bytes
- **Status Byte 0-35 Discrete** (`sensor.alta80_byte_0_discrete` to `sensor.alta80_byte_35_discrete`): Raw status bytes for discrete visualization
  - No state class (enables horizontal bar chart history)
  - Same data as line graph version but optimized for discrete value visualization
  - Ideal for history cards showing state changes over time

#### 🔘 Controls & Set Points

> [!WARNING]  
> Currently, these controls are not functioning reliably. The current state of the device for some controls are also not available, so they will not update correctly in the UI.

**System Controls:**

- **Power** (`switch.alta80_power`): Turn device on/off
- **Eco Mode** (`switch.alta80_eco_mode`): Enable/disable eco-mode
- **Battery Protection** (`select.alta80_battery_protection`): Set protection level (Low, Medium, High)

**Temperature Controls:**

- **Zone 1 Set Point** (`number.alta80_zone1_setpoint`): Temperature slider control (-4 °F to 68 °F)
- **Zone 2 Set Point** (`number.alta80_zone2_setpoint`): Temperature slider control (-4 °F to 68 °F)

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
type: history-graph
entities:
  - entity: sensor.gzf1_80_<serial number>_status_byte_2
    name: B2
  - entity: sensor.gzf1_80_<serial number>_status_byte_3
    name: B3
  - entity: sensor.gzf1_80_<serial number>_status_byte_4
    name: B4
  - entity: sensor.gzf1_80_<serial number>_status_byte_5
    name: B5
  - entity: sensor.gzf1_80_<serial number>_status_byte_6
    name: B6
  - entity: sensor.gzf1_80_<serial number>_status_byte_7
    name: B7
  - entity: sensor.gzf1_80_<serial number>_status_byte_8
    name: B8
  - entity: sensor.gzf1_80_<serial number>_status_byte_9
    name: B9
  - entity: sensor.gzf1_80_<serial number>_status_byte_10
    name: B10
  - entity: sensor.gzf1_80_<serial number>_status_byte_11
    name: B11
  - entity: sensor.gzf1_80_<serial number>_status_byte_12
    name: B12
  - entity: sensor.gzf1_80_<serial number>_status_byte_15
    name: B15
  - entity: sensor.gzf1_80_<serial number>_status_byte_16
    name: B16
  - entity: sensor.gzf1_80_<serial number>_status_byte_17
    name: B17
  - entity: sensor.gzf1_80_<serial number>_status_byte_18
    name: B18
  - entity: sensor.gzf1_80_<serial number>_status_byte_21
    name: B21
  - entity: sensor.gzf1_80_<serial number>_status_byte_22
    name: B22
  - entity: sensor.gzf1_80_<serial number>_status_byte_23
    name: B23
  - entity: sensor.gzf1_80_<serial number>_status_byte_24
    name: B24
  - entity: sensor.gzf1_80_<serial number>_status_byte_27
    name: B27
  - entity: sensor.gzf1_80_<serial number>_status_byte_28
    name: B28
  - entity: sensor.gzf1_80_<serial number>_status_byte_29
    name: B29
  - entity: sensor.gzf1_80_<serial number>_status_byte_30
    name: B30
  - entity: sensor.gzf1_80_<serial number>_status_byte_31
    name: B31
  - entity: sensor.gzf1_80_<serial number>_status_byte_32
    name: B32
  - entity: sensor.gzf1_80_<serial number>_status_byte_33
    name: B33
  - entity: sensor.gzf1_80_<serial number>_status_byte_34
    name: B34
  - entity: sensor.gzf1_80_<serial number>_status_byte_35
    name: B35
title: Bytes
hours_to_show: 1

```

## 🏗️ Architecture

### Component Overview

```
goalzero_ble/
├── __init__.py             # Integration setup and entry point
├── config_flow.py          # Configuration UI and device discovery
├── coordinator.py          # Data update coordination
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
2. **Create Branch**: Use descriptive branch names (`feature/yeti-300x-support`)
3. **Code Standards**: Follow existing code style and patterns
4. **Test Changes**: Verify with real devices when possible
5. **Documentation**: Update README and inline documentation
6. **Pull Request**: Submit with clear description of changes

## 🤝 Contributing

Contributions are greatly appreciated! Here's how you can help:

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

## 📄 License

This project is licensed under the CC BY-NC-SA 4.0 [Attribution-NonCommercial-ShareAlike](https://creativecommons.org/licenses/by-nc-sa/4.0/) license.

## Status Response Protocol Details

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

- **Power State (Byte 4)**: TBD
- **Eco Mode (Byte 5)**: TBD
- **Battery Protection (Byte 6)**: TBD

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

#### Future Research Areas

1. **Error Codes**: Identifying fault and diagnostic information

## �🙏 Acknowledgments

- **Home Assistant Community**: For the excellent platform and development tools
- **Goal Zero**: For creating innovative portable power solutions
- **HACS**: For simplifying custom integration distribution
- **Bleak**: For robust Python BLE communication capabilities
- **Contributors**: Everyone who has tested, reported issues, and contributed code

---

**⭐ If this integration helps you monitor your Goal Zero devices, please give it a star!**

For support, feature requests, or bug reports, please [open an issue](https://github.com/mattxcnm/goalzero_ble/issues) on GitHub.

## ⚖️ Legal Disclaimer

> [!CAUTION] IMPORTANT:
> READ BEFORE USE

This project is an independent, unofficial integration developed without authorization, endorsement, or support from Goal Zero LLC, BioLite Inc., or any of their affiliates. This software is provided "AS IS" without warranty of any kind.

### Liability and Warranty Disclaimer

**NO WARRANTIES**: This software is provided without any express or implied warranties, including but not limited to warranties of merchantability, fitness for a particular purpose, or non-infringement. The author makes no guarantees regarding the software's functionality, reliability, or safety.

**LIMITATION OF LIABILITY**: Under no circumstances shall the author, contributors, or any associated parties be liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including but not limited to procurement of substitute goods or services, loss of use, data, or profits, business interruption, device damage, or personal injury) however caused and on any theory of liability, whether in contract, strict liability, or tort (including negligence or otherwise) arising in any way out of the use of this software, even if advised of the possibility of such damage.

### Device and Safety Considerations

**USE AT YOUR OWN RISK**: Bluetooth communication with electronic devices carries inherent risks. Users assume full responsibility for any damage to their Goal Zero devices, connected equipment, or personal property resulting from the use of this integration.

**NO OFFICIAL SUPPORT**: This integration is not supported by Goal Zero or BioLite. Do not contact these companies for support related to this software. Use of this integration may void your device warranty.

**ELECTRICAL SAFETY**: Goal Zero devices handle significant electrical power. Improper use or control through unofficial software could potentially result in device malfunction, electrical hazards, or safety risks. Users are responsible for ensuring safe operation.

### Intellectual Property

This project does not claim any ownership of Goal Zero, BioLite, or related trademarks, trade names, or intellectual property. All product names, logos, and brands are property of their respective owners. This project is developed for educational and personal use purposes under fair use principles.

### Compliance and Legal Use

Users are responsible for ensuring their use of this software complies with all applicable local, state, federal, and international laws and regulations. The author assumes no responsibility for any legal issues arising from the use of this software.

**By using this software, you acknowledge that you have read, understood, and agree to be bound by this disclaimer and accept all associated risks.**