"""Test the Birthday Calendar config flow."""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.birthday_calendar.const import (
    CONF_CALENDAR_NAME,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    DOMAIN,
)


async def test_form(hass, aioclient_mock):
    """Test we get the form."""
    aioclient_mock.request("PROPFIND", "http://test.local", status=200)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CALENDAR_NAME: "Test Calendar",
            CONF_URL: "http://test.local",
            CONF_USERNAME: "test-user",
            CONF_PASSWORD: "test-password",
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Calendar"
    assert result2["data"] == {
        CONF_CALENDAR_NAME: "Test Calendar",
        CONF_URL: "http://test.local",
        CONF_USERNAME: "test-user",
        CONF_PASSWORD: "test-password",
        "days": 30,
    }


async def test_form_invalid_auth(hass, aioclient_mock):
    """Test invalid auth."""
    aioclient_mock.request("PROPFIND", "http://test.local", status=401)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CALENDAR_NAME: "Test Calendar",
            CONF_URL: "http://test.local",
            CONF_USERNAME: "test-user",
            CONF_PASSWORD: "test-password",
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass, aioclient_mock):
    """Test cannot connect."""
    aioclient_mock.request("PROPFIND", "http://test.local", status=500)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CALENDAR_NAME: "Test Calendar",
            CONF_URL: "http://test.local",
            CONF_USERNAME: "test-user",
            CONF_PASSWORD: "test-password",
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
