"""
pms.hotel_chatbot.main_chatbot
Main routing chatbot that coordinates specialized chatbots.

Enhanced with robust error handling, proper window management,
and comprehensive documentation.

Features:
- Role-based chatbot routing
- Dynamic module loading
- Graceful error recovery
- Window state management
- Session persistence
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error
import datetime
import threading
import time
import logging

# Configure logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MainChatbot')

# Robust import handling with multiple fallback strategies
try:
    # Primary import - standard package structure
    from pms.hotel_chatbot.base_chatbot import BaseChatbot
except ModuleNotFoundError as e:
    logger.warning(f"Primary import failed: {e}, attempting fallback paths...")
    
    # Fallback 1: Project root import
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    potential_paths = [
        project_root,  # Standard project structure
        os.path.join(project_root, 'pms'),  # Direct pms package
        os.path.dirname(current_dir),  # Parent directory
    ]
    
    for path in potential_paths:
        if path not in sys.path and os.path.exists(path):
            sys.path.insert(0, path)
            logger.info(f"Added to sys.path: {path}")
    
    try:
        from hotel_chatbot.base_chatbot import BaseChatbot
        logger.info("Successfully imported via fallback path")
    except ModuleNotFoundError:
        try:
            from base_chatbot import BaseChatbot
            logger.info("Successfully imported via direct fallback")
        except ModuleNotFoundError as final_error:
            logger.error(f"All import attempts failed: {final_error}")
            raise ImportError(
                "Cannot import BaseChatbot. Please ensure the project structure is correct.\n"
                f"Current sys.path: {sys.path}"
            ) from final_error


class MainChatbot(BaseChatbot):
    """
    Main routing chatbot that coordinates specialized hotel PMS chatbots.
    
    Responsibilities:
    - Route users to appropriate specialized chatbots based on role/intent
    - Manage window state transitions between chatbots
    - Provide general hotel information and help
    - Maintain session persistence and error recovery
    """
    
    def __init__(self, master=None, db_config=None):
        """
        Initialize the main chatbot router.
        
        Args:
            master: Parent tkinter window
            db_config: Database configuration dictionary
        """
        super().__init__(master, db_config, role="Main")
        self.current_specialized_chat = None
        self.chat_history = []
        
        # Enhance UI for better user experience
        self._enhance_ui()
        logger.info("MainChatbot initialized successfully")

    def _enhance_ui(self):
        """Add UI enhancements for better user experience."""
        if hasattr(self, 'text_widget') and self.text_widget:
            # Configure tags for better text formatting
            self.text_widget.tag_configure('title', font=('Arial', 12, 'bold'), 
                                         foreground='#2E86AB')
            self.text_widget.tag_configure('command', font=('Arial', 10, 'bold'), 
                                         foreground='#A23B72')
            self.text_widget.tag_configure('success', foreground='#28A745')
            self.text_widget.tag_configure('error', foreground='#DC3545')
            
            # Display welcome message with formatting
            self._display_welcome_message()

    def _display_welcome_message(self):
        """Display a formatted welcome message."""
        welcome_text = """🏨 HOTEL MANAGEMENT SYSTEM - MAIN CHATBOT

I'm your central assistant for hotel operations. I can connect you with specialized chatbots for different departments and shifts.

Type 'help' to see available commands or specify which department you need."""
        
        self.display_message(welcome_text, message_type='info')

    def handle_intent(self, text: str) -> str:
        """
        Route user commands to specialized chatbots or handle general intents.
        
        Args:
            text: User input text to analyze and route
            
        Returns:
            str: Response message indicating action taken
        """
        original_text = text
        text = text.lower().strip()
        self.chat_history.append(f"User: {original_text}")
        
        logger.info(f"Processing intent: '{original_text}'")

        try:
            # Route to specialized chatbots
            route_result = self._route_to_specialized_chat(text)
            if route_result:
                return route_result

            # Handle general commands
            general_result = self._handle_general_commands(text)
            if general_result:
                return general_result

            # Fallback with suggestions
            return self._provide_fallback_suggestions(text)

        except Exception as e:
            logger.error(f"Error handling intent '{text}': {str(e)}")
            return f"❌ System error: {str(e)}\nPlease try again or type 'help' for assistance."

    def _route_to_specialized_chat(self, text: str) -> str:
        """
        Route user to appropriate specialized chatbot based on input.
        
        Args:
            text: Normalized user input text
            
        Returns:
            str: Routing result message or None if no route matched
        """
        routing_map = {
            'reception morning': {
                'module': 'pms.hotel_chatbot.reception.morning_chat',
                'class': 'ReceptionMorningChat',
                'description': 'Reception Morning Chat'
            },
            'reception afternoon': {
                'module': 'pms.hotel_chatbot.reception.afternoon_chat',
                'class': 'ReceptionAfternoonChat',
                'description': 'Reception Afternoon Chat'
            },
            'reception night': {
                'module': 'pms.hotel_chatbot.reception.night_chat',
                'class': 'ReceptionNightChat',
                'description': 'Reception Night Chat'
            },
            'housekeeping': {
                'module': 'pms.hotel_chatbot.housekeeping.housekeeping_chat',
                'class': 'HousekeepingChat',
                'description': 'Housekeeping Chat'
            },
            'manager': {
                'module': 'pms.hotel_chatbot.manager.manager_chat',
                'class': 'ManagerChat',
                'description': 'Manager Chat'
            }
        }

        for key, chat_info in routing_map.items():
            if key in text:
                return self._launch_specialized_chat(chat_info)
        
        return None

    def _launch_specialized_chat(self, chat_info: dict) -> str:
        """
        Dynamically launch a specialized chatbot.
        
        Args:
            chat_info: Dictionary containing module, class, and description info
            
        Returns:
            str: Success message or error message
        """
        try:
            # Import the specialized chat module
            module = __import__(chat_info['module'], fromlist=[chat_info['class']])
            chat_class = getattr(module, chat_info['class'])
            
            # Hide main window before launching new chat
            if self.master:
                self.master.withdraw()
            
            # Launch the specialized chatbot
            self.current_specialized_chat = chat_class(
                master=self.master, 
                db_config=self.db_config,
                main_chatbot_callback=self._return_to_main_chat
            )
            
            logger.info(f"Successfully launched {chat_info['description']}")
            return f"✅ Opening {chat_info['description']}..."

        except ImportError as e:
            logger.error(f"Module import failed for {chat_info['module']}: {e}")
            return f"❌ Cannot open {chat_info['description']}: Module not available.\nPlease check installation."
        
        except Exception as e:
            logger.error(f"Failed to launch {chat_info['description']}: {e}")
            return f"❌ Error opening {chat_info['description']}: {str(e)}"

    def _return_to_main_chat(self):
        """
        Callback function to return to main chat from specialized chatbots.
        
        This is called when specialized chats close to restore the main interface.
        """
        logger.info("Returning to main chat")
        if self.master:
            self.master.deiconify()  # Show main window
        
        self.current_specialized_chat = None
        
        # Refresh and show welcome back message
        if hasattr(self, 'text_widget') and self.text_widget:
            self.display_message(
                "\n🔙 Welcome back to Main Chat!\nHow can I assist you?",
                message_type='success'
            )

    def _handle_general_commands(self, text: str) -> str:
        """
        Handle general commands that don't require specialized chatbots.
        
        Args:
            text: Normalized user input text
            
        Returns:
            str: Command response or None if no command matched
        """
        command_handlers = {
            'help': self.get_help_text,
            '?': self.get_help_text,
            'commands': self.get_help_text,
            'status': self.get_system_status,
            'history': self.get_chat_history,
            'clear': self.clear_chat,
            'exit': self.exit_application,
        }

        for command, handler in command_handlers.items():
            if text == command:
                return handler()
        
        return None

    def _provide_fallback_suggestions(self, text: str) -> str:
        """
        Provide helpful suggestions when no intent is matched.
        
        Args:
            text: Original user input text
            
        Returns:
            str: Helpful error message with suggestions
        """
        suggestions = []
        
        # Keyword-based suggestions
        keywords = {
            'check': 'reception',
            'room': 'reception or housekeeping',
            'clean': 'housekeeping', 
            'report': 'manager',
            'guest': 'reception',
            'reservation': 'reception'
        }
        
        for keyword, suggestion in keywords.items():
            if keyword in text:
                suggestions.append(f"Try '{suggestion}' for {keyword}-related tasks")
        
        # Default fallback message
        if not suggestions:
            base_message = "Sorry, I didn't understand that command."
        else:
            base_message = "I think you might be looking for:"
        
        help_suggestion = "\nType 'help' to see all available commands."
        
        if suggestions:
            return f"❌ {base_message}\n" + "\n".join(f"• {s}" for s in suggestions) + help_suggestion
        else:
            return f"❌ {base_message}{help_suggestion}"

    def get_help_text(self) -> str:
        """Return comprehensive help text with formatted commands."""
        return """
🏨 **MAIN CHATBOT - AVAILABLE COMMANDS**

**Department Access:**
• `reception morning` - Morning shift reception tasks
• `reception afternoon` - Afternoon shift reception tasks  
• `reception night` - Night shift reception tasks
• `housekeeping` - Room cleaning and maintenance
• `manager` - Reports and administrative functions

**General Commands:**
• `help` / `commands` - Show this help message
• `status` - Show system status
• `history` - Show chat history
• `clear` - Clear chat window
• `exit` - Close application

**Need help?** Just mention what you want to do (check-in, clean room, etc.)
"""

    def get_system_status(self) -> str:
        """Return current system status and database connection info."""
        try:
            db_status = "✅ Connected" if self.test_connection() else "❌ Disconnected"
            
            status_info = [
                f"🖥️  SYSTEM STATUS",
                f"Database: {db_status}",
                f"Active Chats: {1 if self.current_specialized_chat else 0}",
                f"Chat History: {len(self.chat_history)} messages",
                f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            return "\n".join(status_info)
            
        except Exception as e:
            return f"❌ Unable to retrieve system status: {str(e)}"

    def get_chat_history(self) -> str:
        """Return recent chat history."""
        if not self.chat_history:
            return "No chat history yet. Start a conversation!"
        
        recent_history = self.chat_history[-10:]  # Last 10 messages
        history_text = "📝 RECENT CHAT HISTORY:\n" + "\n".join(
            f"{i+1}. {msg}" for i, msg in enumerate(recent_history)
        )
        
        return history_text

    def clear_chat(self) -> str:
        """Clear the chat display."""
        if hasattr(self, 'text_widget') and self.text_widget:
            self.text_widget.delete('1.0', tk.END)
            self._display_welcome_message()
            return "Chat cleared."
        return "Unable to clear chat."

    def exit_application(self) -> str:
        """Safely exit the application."""
        if self.master:
            self.master.quit()
        return "Goodbye! Closing application..."

    def display_message(self, message: str, message_type: str = 'info'):
        """
        Enhanced message display with formatting.
        
        Args:
            message: Text to display
            message_type: Type of message ('info', 'success', 'error', 'command')
        """
        if hasattr(self, 'text_widget') and self.text_widget:
            # Apply formatting based on message type
            tag = message_type if message_type in ['success', 'error', 'command'] else 'info'
            
            self.text_widget.insert(tk.END, f"\n{message}\n", tag)
            self.text_widget.see(tk.END)
            self.text_widget.update()


def _demo_run():
    """
    Demo entry point for standalone testing with enhanced error handling.
    """
    print("🚀 Starting MainChatbot Demo...")
    
    # Demo database configuration
    demo_db = {
        'host': 'localhost',
        'user': 'adm',
        'password': '&azertyt',
        'database': 'management',
        'port': 3306
    }

    try:
        # Initialize and run the application
        root = tk.Tk()
        root.title("Hotel PMS - Main Chatbot")
        root.geometry("600x500")
        
        app = MainChatbot(master=root, db_config=demo_db)
        
        print("✅ MainChatbot demo started successfully")
        print("💡 Type commands in the chat window or use 'help' for options")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Demo failed to start: {e}")
        # Provide helpful debugging information
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")


if __name__ == "__main__":
    _demo_run()