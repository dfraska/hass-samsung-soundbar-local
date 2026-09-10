"""Media Player entity for Samsung Soundbar Local."""

from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .soundbar import AsyncSoundbar

_LOGGER = logging.getLogger(__name__)

_SUPPORTED: MediaPlayerEntityFeature = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
)

_SOURCES = {
    "PC": "HDMI_IN1",
    "HDMI 2": "HDMI_IN2",
    "TV (eARC)": "E_ARC",
    "TV (ARC)": "ARC",
    "Optical": "D_IN",
    "Bluetooth": "BT",
    "Wi-Fi": "WIFI_IDLE",
}

_SOUND_MODES = {
    "Standard": "STANDARD",
    "Surround": "SURROUND",
    "Game Pro": "GAME",
    "Adaptive Sound": "ADAPTIVE",
}

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    """Set up the soundbar platform from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    soundbar: AsyncSoundbar = data["soundbar"]

    async_add_entities([SoundbarLocalEntity(coordinator, soundbar, entry)], True)


class SoundbarLocalEntity(CoordinatorEntity, MediaPlayerEntity):
    """Representation of the soundbar as a Media Player entity."""

    _attr_supported_features = _SUPPORTED
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_source_list = list(_SOURCES)
    _attr_sound_mode_list = list(_SOUND_MODES)

    def __init__(self, coordinator, soundbar: AsyncSoundbar, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._soundbar = soundbar
        self._entry = entry

        host = entry.data["host"]
        self._attr_unique_id = host
        self._attr_name = f"Soundbar {host}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            manufacturer="Samsung",
            model="Soundbar",
            name=self._attr_name,
        )

    # ---------- control ----------
    async def async_turn_on(self) -> None:
        await self._soundbar.power_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self._soundbar.power_off()
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        await self._soundbar.volume_up()
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        await self._soundbar.volume_down()
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        await self._soundbar.set_volume(int(volume * 100))
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        if mute != self.is_volume_muted:
            await self._soundbar.mute_toggle()
            await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        await self._soundbar.select_input(_SOURCES[source])
        await self.coordinator.async_request_refresh()

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        await self._soundbar.set_sound_mode(_SOUND_MODES[sound_mode])
        await self.coordinator.async_request_refresh()

    # ---------- properties ----------
    @property
    def state(self):
        power = self.coordinator.data.get("power")
        return STATE_ON if power == "powerOn" else STATE_OFF

    @property
    def volume_level(self):
        return self.coordinator.data.get("volume", 0) / 100

    @property
    def is_volume_muted(self):
        return self.coordinator.data.get("mute", False)

    @property
    def source(self):
        input_name = self.coordinator.data.get("input")
        return next(
            (friendly for friendly, samsung in _SOURCES.items() if samsung == input_name),
            input_name,
        )

    @property
    def sound_mode(self):
        mode = self.coordinator.data.get("sound_mode")
        return next(
            (friendly for friendly, samsung in _SOUND_MODES.items() if samsung == mode),
            mode,
        )

    # ---------- coordinator update ----------
    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
