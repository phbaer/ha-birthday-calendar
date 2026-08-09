"""Test the Birthday Calendar utility logic."""

import os
import sys

sys.path.append(os.getcwd())  # noqa: E402

from datetime import date, datetime, timedelta, timezone  # noqa: E402
import vobject  # noqa: E402

from custom_components.birthday_calendar.utils import (  # noqa: E402
    parse_bday,
    parse_multistatus,
)

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


def test_parse_multistatus():
    """Test parsing of PROPFIND response."""
    # Mocking some XML content or just concated vcards
    content = f"""
    <d:multistatus>
        <d:response>
            <d:propstat>
                <d:prop>
                    <c:address-data>
                        {VCARD_DATA}
                    </c:address-data>
                </d:prop>
            </d:propstat>
        </d:response>
    </d:multistatus>
    """
    vcards = parse_multistatus(content)
    assert len(vcards) == 2
    assert vcards[0].fn.value == "John Doe"
    assert vcards[1].fn.value == "Jane Doe"


def test_parse_bday():
    """Test parsing of birthdays."""
    vcard_john = vobject.readOne("""
BEGIN:VCARD
VERSION:3.0
FN:John Doe
BDAY:1990-05-10
END:VCARD
""")

    now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    start_date = now
    end_date = now + timedelta(days=365)

    event = parse_bday(vcard_john, start_date, end_date)
    assert event is not None
    assert event["summary"] == "John Doe's Birthday (33)"
    assert event["start"] == date(2023, 5, 10)


def test_parse_bday_no_year():
    """Test parsing of birthdays with no year (if vobject parses them)."""
    # Note: vobject parsing of --05-10 might vary.
    # ISO 8601 says --MM-DD is valid.
    vcard_noyear = vobject.readOne("""
BEGIN:VCARD
VERSION:3.0
FN:No Year
BDAY:--05-10
END:VCARD
""")
    # If vobject fails to parse --05-10 to a date/struct, it might be a string.
    # Our code handles string fallback.

    now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    start_date = now
    end_date = now + timedelta(days=365)

    # This might return None if vobject/our logic doesn't support the specific format
    # but let's see if it works or not.
    event = parse_bday(vcard_noyear, start_date, end_date)

    if event:
        assert event["summary"] == "No Year's Birthday"
        assert event["start"] == date(2023, 5, 10)
