# departments/base.py
from dataclasses import dataclass
from enum import Enum

class Shift(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"

@dataclass
class DepartmentContext:
    department: str
    shift: Shift