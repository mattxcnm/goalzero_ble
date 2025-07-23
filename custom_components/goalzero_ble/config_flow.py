"""Config flow for Goal Zero BLE integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DEFAULT_NAME
from .devices import detect_device_type

_LOGGER = logging.getLogger(__name__)


class GoalZeroBLEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Goal Zero BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, dict[str, str]] = {}

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle bluetooth discovery."""
        address = discovery_info.address
        device_name = discovery_info.name or DEFAULT_NAME

        # Detect device type
        device_type = detect_device_type(device_name, discovery_info.manufacturer_data)
        if not device_type:
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self._discovered_devices[address] = {
            "name": device_name,
            "type": device_type,
        }
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            address = self.unique_id
            device_info = self._discovered_devices[address]
            return self.async_create_entry(
                title=device_info["name"],
                data={
                    CONF_ADDRESS: address,
                    CONF_NAME: device_info["name"],
                    "device_type": device_info["type"],
                },
            )

        device_info = self._discovered_devices[self.unique_id]
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": device_info["name"],
                "type": device_info["type"],
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Try to detect device type from name
            device_type = detect_device_type(user_input[CONF_NAME])
            if not device_type:
                device_type = "yeti500"  # Default fallback

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    **user_input,
                    "device_type": device_type,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): str,
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
        )
