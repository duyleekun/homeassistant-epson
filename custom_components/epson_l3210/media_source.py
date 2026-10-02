from __future__ import annotations

from pathlib import Path

from homeassistant.components.media_player import BrowseError, MediaClass
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN, OUTPUT_DIR, SCAN_FILE_SUFFIXES


async def async_get_media_source(hass: HomeAssistant) -> "EpsonMediaSource":
    return EpsonMediaSource(hass)


def _safe_path(identifier: str) -> Path:
    path = (OUTPUT_DIR / Path(identifier).name).resolve()
    if path.parent != OUTPUT_DIR.resolve() or path.suffix.lower() not in SCAN_FILE_SUFFIXES:
        raise BrowseError("Unknown scan")
    return path


class EpsonMediaSource(MediaSource):
    name = "Epson scans"

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        if item.identifier:
            path = _safe_path(item.identifier)
            if not path.is_file():
                raise BrowseError("Scan not found")
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=path.name,
                media_class=MediaClass.IMAGE,
                media_content_type="image/jpeg",
                title=path.name,
                can_play=True,
                can_expand=False,
            )
        try:
            files = await self.hass.async_add_executor_job(
                lambda: sorted(
                    [
                        path
                        for path in OUTPUT_DIR.iterdir()
                        if path.is_file() and path.suffix.lower() in SCAN_FILE_SUFFIXES
                    ],
                    key=lambda path: path.stat().st_mtime,
                    reverse=True,
                )
            )
        except OSError:
            files = []
        children = [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=path.name,
                media_class=MediaClass.IMAGE,
                media_content_type="image/jpeg",
                title=path.name,
                can_play=True,
                can_expand=False,
            )
            for path in files
        ]
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.DIRECTORY,
            media_content_type="",
            title="Epson scans",
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.IMAGE,
            children=children,
        )

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        path = _safe_path(item.identifier)
        if not path.is_file():
            raise BrowseError("Scan not found")
        return PlayMedia(str(path), "image/jpeg")
