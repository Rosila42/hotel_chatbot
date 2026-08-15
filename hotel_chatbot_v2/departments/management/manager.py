from __future__ import annotations


class ManagementChat:
    """Management workflow context; reporting and PMS operations remain service-owned."""

    department = "management"

    def can_view_operational_summary(self) -> bool:
        return True
