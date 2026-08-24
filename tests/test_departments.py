import pytest

from departments.base import DepartmentContext, Shift
from departments.housekeeping import HousekeepingChat
from departments.management import ManagementChat
from departments.reception.reception import ReceptionChat


def test_department_context_normalizes_values():
    context = DepartmentContext(" Reception ", "MORNING")

    assert context.department == "reception"
    assert context.shift is Shift.MORNING


def test_department_context_rejects_unknown_shift():
    with pytest.raises(ValueError):
        DepartmentContext("reception", "graveyard")


def test_reception_uses_one_context_model_for_all_shifts():
    morning = ReceptionChat("MORNING")
    night = ReceptionChat(Shift.NIGHT)

    assert morning.shift == "morning"
    assert night.shift == "night"
    assert morning.department_context.department == "reception"
    assert morning.get_context()["shift_name"] == "Morning"


def test_reception_shift_hints_do_not_modify_shared_sources():
    reception = ReceptionChat("morning")
    context = reception.get_context()
    context["suggested_prompts"].append("unexpected")

    assert "unexpected" not in reception.get_context()["suggested_prompts"]


def test_housekeeping_has_department_context_without_shift():
    housekeeping = HousekeepingChat()

    assert housekeeping.context.department == "housekeeping"
    assert housekeeping.context.shift is None
    assert housekeeping.can_mark_room_clean() is True


def test_management_has_department_context_without_shift():
    management = ManagementChat()

    assert management.context.department == "management"
    assert management.context.shift is None
    assert management.can_view_operational_summary() is True
