"""Config flow for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_DEVICE_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
)
from .device_registry import DeviceRegistry

_LOGGER = logging.getLogger(__name__)


class GoalZeroBLEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Goal Zero BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_device: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle bluetooth discovery."""
        _LOGGER.debug("Bluetooth discovery triggered for %s", discovery_info.name)
        
        device_name = discovery_info.name
        address = discovery_info.address

        if not device_name:
            _LOGGER.debug("Device has no name, ignoring")
            return self.async_abort(reason="no_name")

        # Check if this is a supported Goal Zero device
        device_type = DeviceRegistry.detect_device_type(device_name)
        if not device_type:
            _LOGGER.debug("Device %s is not a supported Goal Zero device", device_name)
            return self.async_abort(reason="not_supported")

        # Set unique ID to device address
        await self.async_set_unique_id(address.replace(":", "").upper())
        self._abort_if_unique_id_configured()

        # Store discovered device info
        self._discovered_device = {
            "name": device_name,
            "address": address,
            "type": device_type,
            "model": DeviceRegistry.get_device_model(device_type),
        }

        # Show confirmation form
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm bluetooth discovery."""
        if user_input is not None:
            update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            
            return self.async_create_entry(
                title=self._discovered_device["name"],
                data={
                    CONF_ADDRESS: self._discovered_device["address"],
                    CONF_DEVICE_NAME: self._discovered_device["name"],
                    CONF_UPDATE_INTERVAL: update_interval,
                    "device_type": self._discovered_device["type"],
                },
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=vol.Schema({
                vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                    cv.positive_int,
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)
                ),
            }),
            description_placeholders={
                "name": self._discovered_device["name"],
                "model": self._discovered_device["model"],
                "address": self._discovered_device["address"],
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual setup."""
        errors = {}

        if user_input is not None:
            device_name = user_input[CONF_DEVICE_NAME].strip()
            update_interval = user_input[CONF_UPDATE_INTERVAL]

            # Validate device name format
            device_type = DeviceRegistry.detect_device_type(device_name)
            if not device_type:
                errors["base"] = "invalid_device_name"
            else:
                # Try to find the device via bluetooth
                try:
                    discovery_info = await bluetooth.async_scanner_by_source(
                        self.hass, bluetooth.BluetoothScanningMode.ACTIVE
                    )
                    
                    found_device = None
                    for device_advertisement in discovery_info.values():
                        for advertisement in device_advertisement.values():
                            if advertisement.name == device_name:
                                found_device = advertisement
                                break
                        if found_device:
                            break
                    
                    if found_device:
                        # Set unique ID and check for duplicates
                        await self.async_set_unique_id(
                            found_device.address.replace(":", "").upper()
                        )
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=device_name,
                            data={
                                CONF_ADDRESS: found_device.address,
                                CONF_DEVICE_NAME: device_name,
                                CONF_UPDATE_INTERVAL: update_interval,
                                "device_type": device_type,
                            },
                        )
                    else:
                        errors["base"] = "device_not_found"
                        
                except Exception as e:
                    _LOGGER.error("Error during device discovery: %s", e)
                    errors["base"] = "cannot_connect"

        # Get device patterns for the form description
        patterns = DeviceRegistry.get_device_patterns()
        pattern_text = "\n".join([f"• {dtype}: {pattern}" for dtype, pattern in patterns.items()])

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_NAME): cv.string,
                vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                    cv.positive_int,
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)
                ),
            }),
            errors=errors,
            description_placeholders={
                "patterns": pattern_text,
                "min_interval": str(MIN_UPDATE_INTERVAL),
                "max_interval": str(MAX_UPDATE_INTERVAL),
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        config_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        
        if user_input is not None:
            return self.async_update_reload_and_abort(
                config_entry,
                data={
                    **config_entry.data,
                    CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                },
            )

        current_interval = config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                    cv.positive_int,
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)
                ),
            }),
            description_placeholders={
                "device_name": config_entry.data.get(CONF_DEVICE_NAME, "Unknown"),
            },
        )
