"""Config flow for NHC integration."""
import logging
from homeassistant import config_entries
from homeassistant.core import callback

DOMAIN = "nhc"
_LOGGER = logging.getLogger(__name__)

class NHCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NHC Storm Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step when a user clicks 'Add Integration'."""
        # Prevent the user from adding your integration more than once
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            # Create the integration entry with a friendly title
            return self.async_create_entry(title="NHC Storm Tracker", data={})

        # Display an empty submit form (no text boxes needed since it's fully automatic)
        return self.async_show_form(step_id="user")

