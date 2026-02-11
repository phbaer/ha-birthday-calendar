"""Utility functions for Birthday Calendar."""

import datetime
from datetime import timedelta
import logging
import re
from typing import Any
import vobject

_LOGGER = logging.getLogger(__name__)


def parse_multistatus(content: str) -> list[Any]:
    """Parse the PROPFIND response to extract vCards."""
    vcards = []
    # Simple regex based extraction to avoid XML deps if possible
    matches = re.findall(r"(BEGIN:VCARD.*?END:VCARD)", content, re.DOTALL)

    for vcard_str in matches:
        try:
            vcard_str = (
                vcard_str.replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
            )
            vcard = vobject.readOne(vcard_str)
            vcards.append(vcard)
        except Exception:  # pylint: disable=broad-except
            continue

    return vcards


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

        if isinstance(bday_val, str):
            try:
                bday_val = datetime.date.fromisoformat(bday_val)
            except ValueError:
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

        age = found_date.year - bday_val.year
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
