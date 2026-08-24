# departments/reception/workflows/morning_arrivals.py
class MorningArrivalsWorkflow:
    """
    Demonstrates: GET_ARRIVALS → GET_ROOM_STATUS → CREATE_INCIDENT → CONFIRM
    """
    steps = [
        "What are today's arrivals?",
        "Which rooms aren't ready?",
        "Report dirty room {room_number}",
        "Confirm",
    ]