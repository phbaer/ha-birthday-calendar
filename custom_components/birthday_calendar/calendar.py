"""Support for Birthday Calendar from CardDAV."""
from __future__ import annotations

import datetime
import logging
from datetime import timedelta

import aiohttp
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt

from .const import CONF_CALENDAR_NAME, CONF_DAYS, CONF_PASSWORD, CONF_URL, CONF_USERNAME
from .utils import parse_multistatus

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Birthday Calendar platform."""
    name = config_entry.data[CONF_CALENDAR_NAME]
    url = config_entry.data[CONF_URL]
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    days = config_entry.data.get(CONF_DAYS, 30)

    session = async_get_clientsession(hass)
    
    async_add_entities([BirthdayCalendarEntity(name, url, username, password, days, session)], True)


class BirthdayCalendarEntity(CalendarEntity):
    """Retrieving birthday events from a CardDAV server."""

    def __init__(self, name, url, username, password, days, session):
        """Create the Birthday Calendar Entity."""
        self._name = name
        self._url = url
        self._username = username
        self._password = password
        self._days = days
        self._session = session
        self._event = None
        self._attr_name = name

    @property
    def event(self):
        """Return the next upcoming event."""
        return self._event

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> list[CalendarEvent]:
        """Get all events in a specific time frame."""
        # We fetch all birthdays, parse, and filter the addressbook in locally memory.
        # CardDAV queries for specific properties like dates in vCards are complex and not always supported.
        
        vcards = await self._fetch_vcards()
        events = []
        
        for vcard in vcards:
            bday_event = self._parse_bday(vcard, start_date, end_date)
            if bday_event:
                events.append(bday_event)
        
        return events

    async def _fetch_vcards(self) -> list[str]:
        """Fetch all vCards from the CardDAV server."""
        headers = {
            "Depth": "1",
            "Content-Type": "application/xml; charset=utf-8"
        }
        data = """
        <d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav">
            <d:prop>
                <d:getetag />
                <c:address-data />
            </d:prop>
        </d:propfind>
        """
        
        auth = aiohttp.BasicAuth(self._username, self._password)
        
        try:
            async with self._session.request("PROPFIND", self._url, data=data, headers=headers, auth=auth) as response:
                if response.status not in (200, 207):
                    _LOGGER.error("Failed to fetch CardDAV data: %s", response.status)
                    return []
                
                return parse_multistatus(await response.text())
                
        except Exception: # pylint: disable=broad-except
            _LOGGER.exception("Error connecting to CardDAV server")
            return []

    def _parse_bday(self, vcard, start_date: datetime.datetime, end_date: datetime.datetime) -> CalendarEvent | None:
        """Parse a vCard and return a CalendarEvent if a birthday falls in the range."""
        from .utils import parse_bday
        event_data = parse_bday(vcard, start_date, end_date)
        
        if event_data:
            return CalendarEvent(
                start=event_data["start"],
                end=event_data["end"],
                summary=event_data["summary"],
                description=event_data["description"],
                location=event_data["location"]
            )
        return None

    async def async_update(self) -> None:
        """Update the entity state (next event)."""
        start = dt.now()
        end = start + timedelta(days=self._days)
        events = await self.async_get_events(self.hass, start, end)
        
        # Sort
        events.sort(key=lambda x: x.start)
         
        if events:
            self._event = events[0]
        else:
            self._event = None
