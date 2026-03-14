"""
ReceptionMorningChatbot
-----------------------
Standalone chatbot for handling morning reception tasks.
"""

try:
    from pms.hotel_chatbot.utils import greet_user, fetch_morning_tasks
except ImportError:
    # fallback for development/testing without package
    import sys
    sys.path.append("..")
    from utils import greet_user, fetch_morning_tasks

class ReceptionMorningChat:
    """
    Chatbot for morning reception staff.
    """

    def __init__(self, operator_name="Guest"):
        self.operator_name = operator_name
        self.commands = {
            "help": self.show_help,
            "tasks": self.show_tasks,
            "greet": self.greet,
            "exit": self.exit_chat,
        }
        self.running = False

    def greet(self):
        """Return a greeting message for the operator."""
        return greet_user(self.operator_name, period="morning")

    def show_help(self):
        """List available commands."""
        return (
            "Available commands:\n"
            "- greet : Receive a greeting.\n"
            "- tasks : Show your morning tasks.\n"
            "- help  : Show this help message.\n"
            "- exit  : Exit this chatbot."
        )

    def show_tasks(self):
        """Fetch and display the operator's morning tasks."""
        tasks = fetch_morning_tasks(self.operator_name)
        if not tasks:
            return "No tasks assigned for this morning."
