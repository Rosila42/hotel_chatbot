from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Identity:
    user_id: str
    role: str
    department: str


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "receptionist": {
        "pms.guest.read",
        "pms.reservation.read",
        "pms.room.read",
        "pms.incident.read",
        "pms.incident.create",
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


class PermissionService:
    def can(self, identity: Identity, permission: str | None) -> bool:
        if permission is None:
            return True
        return permission in ROLE_PERMISSIONS.get(identity.role, set())

    def permissions_for(self, identity: Identity) -> set[str]:
        return set(ROLE_PERMISSIONS.get(identity.role, set()))
