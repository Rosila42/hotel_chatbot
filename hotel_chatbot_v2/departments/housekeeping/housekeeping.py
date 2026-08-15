from __future__ import annotations


class HousekeepingChat:
    """Housekeeping workflow context. Shared PMS capabilities remain service-owned."""

    department = "housekeeping"

    def can_mark_room_clean(self) -> bool:
        return True
