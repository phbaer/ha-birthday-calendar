"""Utility functions for Birthday Calendar."""

import datetime
from datetime import timedelta
import logging
import re
from typing import Any

from defusedxml import ElementTree

import vobject

_LOGGER = logging.getLogger(__name__)


def parse_multistatus(content: str) -> list[Any]:
    """Parse the PROPFIND response to extract vCards."""
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError:
        _LOGGER.warning("CardDAV server returned an invalid multistatus response")
        # Some CardDAV proxies return the address-data body directly rather
        # than wrapping it in a DAV multistatus response.
        address_data: list[str] = [content]
    else:
        address_data = []
        for element in root.iter():
            if (
                element.tag.rsplit("}", maxsplit=1)[-1] == "address-data"
                and element.text
            ):
                address_data.append(element.text)

    vcards: list[Any] = []
    for vcard_str in address_data:
        # CardDAV may return more than one vCard in a single address-data
        # element.  ``readOne`` only accepts one component, so split the
        # payload into complete VCARD blocks before parsing it.
        card_blocks = re.findall(
            r"BEGIN:VCARD\s.*?END:VCARD", vcard_str, flags=re.IGNORECASE | re.DOTALL
        )
        for card_block in card_blocks:
            try:
                vcards.append(vobject.readOne(card_block))
            except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                _LOGGER.debug("Skipping invalid vCard returned by CardDAV server")

    return vcards


# vObject accepts several date representations and can raise parser-specific
# exceptions, so this function deliberately keeps the defensive fallback.
# pylint: disable=too-many-locals,too-many-branches
def parse_bday(
    vcard: Any,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
) -> dict[str, Any] | None:
    """Parse a vCard for birthday events.

    Returns a dictionary with event details if a birthday falls in the range.

    Returns None or dict with keys:
    start, end, summary, description, location
    """
    if not hasattr(vcard, "bday"):
        return None

    try:
        bday_val = vcard.bday.value

        has_birth_year = True
        if isinstance(bday_val, datetime.datetime):
            bday_val = bday_val.date()
        elif isinstance(bday_val, datetime.date):
            # vobject normally returns a date for a full-year BDAY.
            pass
        elif isinstance(bday_val, str):
            try:
                bday_val = datetime.date.fromisoformat(bday_val)
            except ValueError:
                try:
                    month, day = map(int, bday_val.removeprefix("--").split("-"))
                    bday_val = datetime.date(2000, month, day)
                    has_birth_year = False
                except (TypeError, ValueError):
                    return None

        if not isinstance(bday_val, datetime.date):
            return None

        current_year = start_date.year

        try:
            candidate = datetime.date(current_year, bday_val.month, bday_val.day)
        except ValueError:
            candidate = datetime.date(current_year, 3, 1)

        found_date = None

        candidates = [
            candidate,
            (
                datetime.date(current_year + 1, candidate.month, candidate.day)
                if candidate.month != 2 or candidate.day != 29
                else datetime.date(current_year + 1, 3, 1)
            ),
        ]

        for d in candidates:
            d_dt = datetime.datetime.combine(d, datetime.time.min).replace(
                tzinfo=start_date.tzinfo
            )
            # Handle naive/aware mismatch if needed
            if start_date.tzinfo and d_dt.tzinfo is None:
                # Check if start_date has tzinfo and use it?
                # Usually HA passes aware start_date
                d_dt = d_dt.replace(tzinfo=start_date.tzinfo)

            d_end = d_dt + timedelta(days=1)

            if d_end > start_date and d_dt < end_date:
                found_date = d
                break

        if not found_date:
            return None

        fn = "Unknown"
        if hasattr(vcard, "fn"):
            fn = vcard.fn.value
        elif hasattr(vcard, "n"):
            fn = str(vcard.n.value).strip()

        summary = f"{fn}'s Birthday"

        age = found_date.year - bday_val.year if has_birth_year else 0
        if age > 0 and bday_val.year > 1900:
            summary += f" ({age})"

        return {
            "start": found_date,
            "end": found_date + timedelta(days=1),
            "summary": summary,
            "description": f"Happy {age}th Birthday!"
            if age > 0 and bday_val.year > 1900
            else "Happy Birthday!",
            "location": "",
        }

    except Exception:  # pylint: disable=broad-except
        return None
