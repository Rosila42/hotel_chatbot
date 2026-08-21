from typing import Any

class ResponseFormatter:
    @staticmethod
    def format(command: str, result_data: Any) -> str:
        if command == "HELP": return "Available commands: " + ", ".join(result_data)
        if command == "GET_SYSTEM_STATUS": return "; ".join(f"{k}: {v}" for k, v in result_data.items())
        if command == "FAQ_SEARCH":
            matches = result_data.get("matches", [])
            if not matches: return "I couldn't find an answer in the approved FAQ content."
            return matches[0]["answer"]
        if isinstance(result_data, list): return f"Found {len(result_data)} result(s)."
        return str(result_data)