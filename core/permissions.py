from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Identity:
    user_id: str
    role: str
    department: str


class PermissionService:
    """Small V1 capability-based permission map.

    Production deployments should derive roles/identity from the host PMS or
    application identity system rather than accepting them from the client.
    """

    ROLE_PERMISSIONS = {
        "receptionist": {
            "pms.guest.read",
            "pms.reservation.read",
            "pms.room.read",
            "pms.incident.read",
        },
        "housekeeper": {
            "pms.room.read",
            "housekeeping.room.update",
            "pms.incident.read",
            "pms.incident.create",
        },
        "manager": {
            "pms.guest.read",
            "pms.reservation.read",
            "pms.room.read",
            "housekeeping.room.update",
            "pms.incident.read",
            "pms.incident.create",
            "pms.incident.resolve",
            "management.reporting.read",
            "automation.read",
            "automation.manage",
            "automation.execute",
        },
    }

    def can(self, identity: Identity, permission: str | None) -> bool:
        if permission is None:
            return True
        return permission in self.ROLE_PERMISSIONS.get(identity.role, set())
