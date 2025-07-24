# Goal Zero BLE Integration

A Home Assistant custom integration for Goal Zero devices via Bluetooth Low Energy (BLE).

## 🚀 Features

- **� Multiple Device Support**: Alta 80 fridge/freezer and Yeti 500 power station
- **📱 Automatic Discovery**: Automatically detects Goal Zero devices via Bluetooth
- **⚙️ Configurable Updates**: Set custom update intervals per device
- **🔧 Modular Architecture**: Easy to extend for future Goal Zero devices  
- **📊 Rich Sensors**: Battery, power, temperature, and status monitoring
- **🎮 Device Controls**: Temperature adjustment, power management, and mode controls
- **🏠 Home Assistant Integration**: Full integration with automations and dashboards

## 📋 Supported Devices

| Device | Model Pattern | Features |
|--------|---------------|----------|
| **Alta 80** | `gzf1-80-XXXXXX` | Battery %, Power consumption, Fridge/Ambient temps, Compressor status, Temperature controls, Power/Eco modes |
| **Yeti 500** | `gzy5c-XXXXXXXXXXXX` | Battery %, Power in/out, Voltage, Current, Power controls |

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

1. Download and copy `custom_components/goalzero_ble/` to your Home Assistant config
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services

## ⚡ Quick Setup

### Automatic Discovery
1. Ensure your Goal Zero device is powered on and in range
2. Go to **Settings** → **Devices & Services** → **Add Integration**
3. The integration will automatically discover nearby Goal Zero devices
4. Click **Configure** when your device appears
5. Set your preferred update interval (10-300 seconds)
6. Click **Submit**

### Manual Setup
1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Goal Zero BLE"
3. Enter your device name exactly (e.g., `gzf1-80-A1B2C3`)
4. Set update interval (10-300 seconds) 
5. Click **Submit**

## 📊 Sensors & Controls

### Alta 80 Fridge/Freezer

**Sensors:**
- Battery percentage
- Power consumption (W)
- Fridge temperature (°C)
- Ambient temperature (°C) 
- Compressor status

**Controls:**
- Temperature up/down
- Power on/off
- Eco mode on/off

### Yeti 500 Power Station

**Sensors:**
- Battery percentage
- Power output (W)
- Power input (W)
- Voltage (V)
- Current (A)

**Controls:**
- Power on/off

## 🔧 Configuration Options

- **Update Interval**: How often to poll the device (10-300 seconds)
- **Device Name**: Exact BLE device name for manual setup

## 🏗️ Architecture

The integration uses a modular device-based architecture:

- **Device Registry**: Handles device detection and type mapping
- **BLE Manager**: Manages Bluetooth connections and GATT communication
- **Device Classes**: Device-specific parsing and command handling
- **Coordinator**: Manages data updates and connection lifecycle
- **Dynamic Entities**: Sensors/buttons are created based on device capabilities

## 🔍 Troubleshooting

### Device Not Found
- Ensure device is powered on and within Bluetooth range
- Check device name matches exactly (case-sensitive)
- Try power cycling the Goal Zero device

### Connection Issues  
- Reduce update interval if experiencing frequent disconnections
- Ensure no other apps are connected to the device
- Check Home Assistant logs for specific error messages

### Sensor Values Unavailable
- Verify device is responding to status requests
- Check that BLE communication is working in HA logs
- Some sensors may not be available depending on device state

## 🚧 Development & Contributions

This integration is designed to be easily extensible for additional Goal Zero devices. To add a new device:

1. Add device pattern to `device_registry.py`
2. Create device class in `devices/` following existing patterns
3. Add GATT handles and commands to constants
4. Update device registry mappings

Pull requests welcome! Please feel free to contribute additional device support or improvements.

## 📚 Protocol Information

The integration uses GATT handles for BLE communication:

- **Commands**: Hex payloads sent to write handles
- **Responses**: Data received from read handles  
- **Parsing**: Device-specific interpretation of response data

Command payloads and response parsing can be customized per device type for future reverse engineering discoveries.

## ⚠️ Disclaimer

This is an unofficial integration not affiliated with Goal Zero. Use at your own risk. Device protocols were reverse-engineered and may change with firmware updates.
