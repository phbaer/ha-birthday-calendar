# Birthday Calendar (CardDAV)

A Home Assistant integration that creates a calendar entity from a CardDAV addressbook, extracting birthdays from contact VCards.

[![CI](https://git.baer.one/phbaer/ha-birthday-calendar/actions/workflows/ci.yaml/badge.svg)](https://git.baer.one/phbaer/ha-birthday-calendar/actions/workflows/ci.yaml)

## Features

-   Connects to any standard CardDAV server (SOGo, Nextcloud, iCloud, etc.).
-   Extracts `BDAY` fields from VCards.
-   Creates a Calendar entity with all birthdays as all-day events.
-   Calculates the next birthday occurrence and current age.
-   Configurable look-ahead period (default 30 days).

## Installation

### HACS

1.  Open HACS.
2.  Add Custom Repository: `https://github.com/phbaer/ha-birthday-calendar`.
3.  Select "Integration".
4.  Install.

### Manual Installation

1.  Download the `birthday-calendar.zip` from the [Latest Release](https://git.baer.one/phbaer/ha-birthday-calendar/releases).
2.  Unzip it.
3.  Copy the `custom_components/birthday-calendar` folder to your Home Assistant `config/custom_components/` directory.
4.  Restart Home Assistant.

## Configuration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for **Birthday Calendar**.
4.  Enter the following details:
    *   **Calendar Name**: Friendly name for the entity.
    *   **CardDAV URL**: Full URL to your addressbook (e.g., `https://example.com/dav/user/contacts/`).
    *   **Username**: CardDAV username.
    *   **Password**: CardDAV password.
    *   **Days to look ahead**: Number of days to include in the calendar view/state (default 30).

## Development

This project uses `uv` for dependency management and requires a recent version of Python (3.13.2+).

### Prerequisites

*   `uv`
*   Python 3.13.2 or later
*   C Compiler (`build-essential`, `gcc`, or `clang`) - **Required** for compiling dependencies on Python 3.14.

### Setup

```bash
uv sync
```

### Testing

Run the full test suite:

```bash
uv run pytest
```

### CI/CD

The project includes a Forgejo/GitHub Actions workflow (`.github/workflows/ci.yaml`) that:
1.  Sets up Python 3.12 and `uv`.
2.  Installs system dependencies (compilers).
3.  Runs tests.
4.  Create a HACS-compatible ZIP release artifact (`birthday_calendar.zip`) on every push and tag.