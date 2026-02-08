"""Test the Birthday Calendar platform (CardDAV)."""
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.birthday_calendar.calendar import BirthdayCalendarEntity
from custom_components.birthday_calendar.const import DOMAIN

VCARD_DATA = """
BEGIN:VCARD
VERSION:3.0
FN:John Doe
N:Doe;John;;;
BDAY:1990-05-10
END:VCARD
BEGIN:VCARD
VERSION:3.0
FN:Jane Doe
N:Doe;Jane;;;
BDAY:1985-02-28
END:VCARD
"""

async def test_calendar_entity(hass: HomeAssistant):
    """Test the calendar entity."""
    
    # Mock aiohttp session and response
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.status = 207
    mock_response.text.return_value = VCARD_DATA
    
    # request() returns a context manager
    mock_request_cm = AsyncMock()
    mock_request_cm.__aenter__.return_value = mock_response
    mock_request_cm.__aexit__.return_value = None
    
    mock_session.request.return_value = mock_request_cm
    
    entity = BirthdayCalendarEntity("Test Calendar", "http://test.local", "user", "pass", 365, mock_session)
    entity.hass = hass
    
    # Test async_get_events
    # Set current time to 2023-01-01
    now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=dt_util.UTC)
    
    with patch("homeassistant.util.dt.now", return_value=now):
        # Determine start/end for the test
        start_date = now
        end_date = now + timedelta(days=365)
        
        events = await entity.async_get_events(hass, start_date, end_date)
        
        # Check that we got events
        assert len(events) == 2
        
        # Sort by start date to predict order
        events.sort(key=lambda x: x.start)
        
        # Jane Doe: Feb 28
        assert events[0].summary == "Jane Doe's Birthday (38)"
        assert events[0].start == date(2023, 2, 28)
        
        # John Doe: May 10
        assert events[1].summary == "John Doe's Birthday (33)"
        assert events[1].start == date(2023, 5, 10)

async def test_calendar_fetch_error(hass: HomeAssistant):
    """Test handling of fetch errors."""
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.status = 500
    
    mock_request_cm = AsyncMock()
    mock_request_cm.__aenter__.return_value = mock_response
    mock_request_cm.__aexit__.return_value = None
    
    mock_session.request.return_value = mock_request_cm
    
    entity = BirthdayCalendarEntity("Test Calendar", "http://test.local", "user", "pass", 30, mock_session)
    entity.hass = hass
    
    events = await entity.async_get_events(hass, dt_util.now(), dt_util.now())
    assert len(events) == 0
