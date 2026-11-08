"""Document access is granted per connection and enforced on the server."""

from homeassistant.auth.models import User
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import CONF_ALLOWED_USERS, DOMAIN


@callback
def can_access(hass: HomeAssistant, entry_id: str, user: User | None) -> bool:
    """Check the current entry options, including on in-flight requests."""
    if user is None or not user.is_active:
        return False
    if user.is_admin:
        return True
    entry = hass.config_entries.async_get_entry(entry_id)
    return bool(
        entry is not None
        and entry.domain == DOMAIN
        and not user.system_generated
        and user.id in allowed_users(entry)
    )


def allowed_users(entry: ConfigEntry) -> list[str]:
    """Read a saved list of user IDs, defaulting to admin-only access."""
    users = entry.options.get(CONF_ALLOWED_USERS, [])
    return users if isinstance(users, list) else []
