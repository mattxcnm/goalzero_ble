# Goal Zero BLE Integration

> **⚠️ WORK IN PROGRESS - NOT FUNCTIONAL YET ⚠️**
> 
> 🚧 **This integration is in active development and does not currently work!** 🚧
> 
> - 🤖 Most code is AI-generated and has not been tested or verified
> - 🔌 BLE communication protocols are not yet implemented
> - 🧪 No device testing has been performed
> - 📋 Consider this a development template/starting point
> 
> **DO NOT USE in production environments!** Contributions and testing welcome!

A Home Assistant custom integration for Goal Zero devices via Bluetooth Low Energy (BLE).

## Supported Devices

- **Yeti 500** - Portable power station with battery and power monitoring
- **Alta 80** - Portable fridge with 2 zones
- **Extensible** - Built to support additional Goal Zero BLE devices

## Features

- 🔋 Battery percentage monitoring
- ⚡ Power consumption/generation tracking
- 📱 Automatic device discovery and identification via Bluetooth
- 🎯 Device-specific sensors and capabilities
- 🏠 Full Home Assistant integration with automations
- 📊 Model-specific data interpretation
- 🔧 HACS compatible

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/mattxcnm/goalzero_ble`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Goal Zero BLE" and install

### Manual Installation

1. Copy the `custom_components/goalzero_ble` folder to your Home Assistant configuration directory
2. Restart Home Assistant
3. Add the integration through the UI

## Configuration

The integration supports automatic discovery of Goal Zero devices via Bluetooth. The integration will automatically detect the device type (Yeti 500, Alta 80, etc.) and configure the appropriate sensors.

Simply go to Settings > Devices & Services > Add Integration and search for "Goal Zero BLE".

## Device-Specific Features

### Yeti 500
- Battery percentage
- Power input/output
- Voltage and current monitoring

### Alta 80
- Zone temperaturatures
- Zone setpoint
- Eco mode on/off
- Battery protection level low/mid/high

## Contributing

Pull requests are welcome! Please feel free to contribute to this project, especially for adding support for additional Goal Zero devices.
