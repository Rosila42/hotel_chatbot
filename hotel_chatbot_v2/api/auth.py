from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import Header, HTTPException

from hotel_chatbot_v2.core.permissions import Identity


@dataclass(frozen=True)
class TokenIdentity:
    token: str
    identity: Identity


# V1/demo authentication only. Production integration should federate identity
# with the host PMS/application and must not accept client-supplied roles.
DEMO_TOKENS = {
    os.getenv("CHATBOT_RECEPTION_TOKEN", "demo-reception-token"): Identity("demo-reception", "receptionist", "reception"),
    os.getenv("CHATBOT_HOUSEKEEPING_TOKEN", "demo-housekeeping-token"): Identity("demo-housekeeping", "housekeeper", "housekeeping"),
    os.getenv("CHATBOT_MANAGER_TOKEN", "demo-manager-token"): Identity("demo-manager", "manager", "management"),
}


def authenticate(authorization: str | None = Header(default=None)) -> Identity:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.removeprefix("Bearer ").strip()
    identity = DEMO_TOKENS.get(token)
    if identity is None:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return identity
