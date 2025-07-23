# Goal Zero BLE Integration

A Home Assistant custom integration for Goal Zero devices via Bluetooth Low Energy (BLE).

## Features

- Battery percentage monitoring
- Power consumption/generation tracking
- Automatic device discovery via Bluetooth
- HACS compatible

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/mattroach/goalzero_ble`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Goal Zero BLE" and install

### Manual Installation

1. Copy the `custom_components/goalzero_ble` folder to your Home Assistant configuration directory
2. Restart Home Assistant
3. Add the integration through the UI

## Configuration

The integration supports automatic discovery of Goal Zero devices via Bluetooth. Simply go to Settings > Devices & Services > Add Integration and search for "Goal Zero BLE".

## Supported Devices

- Goal Zero Yeti series power stations
- Other Goal Zero devices with BLE capability

## Contributing

Pull requests are welcome! Please feel free to contribute to this project.
