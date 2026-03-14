import tkinter as tk
from tkinter import scrolledtext
import requests
import re
import mysql.connector

class ChatbotWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Hotel Staff Chatbot")
        self.master.geometry("600x400")

        self.chat_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=70, height=20)
        self.chat_area.pack(padx=10, pady=10)

        self.user_input = tk.Entry(self.master, width=60)
        self.user_input.pack(side=tk.LEFT, padx=(10, 0), pady=(0, 10))

        self.send_button = tk.Button(self.master, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=(5, 10), pady=(0, 10))

        self.chat_area.insert(tk.END, f"Bot: {self.help_response()}\n\n")




    # --- Database Connection ---
    def connect_db():
        return mysql.connector.connect(
            host="localhost",
            user="adm",
            password="&azertyt",
            database="management"
        )


    #need to print help message at the start
    # ------------- HELP DETECTION & RESPONSE -------------
    def detect_help_request(message):
        return "help" in message.lower()

    #improve help message
    #after ten faq question and the chat is good to go and integrate with PMS
    staff_faq_intents = {
        "reservation not showing": "🔍 Double-check the guest's name, dates, and booking channel. Try other spelling variants or OTAs. If still missing, create it manually and apologize for the confusion.",
        "room not ready": "🧹 Apologize and check with housekeeping. Offer a complimentary drink or alternative room if delay is long.",
        "key not working": "🔑 Try re-encoding or a new card. If it fails again, notify maintenance and stay with the guest.",
        "lost key": "🛡️ Verify ID, deactivate the old key, and issue a new one. Inform the guest if a fee applies.",
        "no show": "📞 Try calling the guest. If unreachable, mark as no-show, apply policy, and update room availability.",
        "guest complaint": "🙏 Apologize, listen carefully, and act fast. Offer room change or compensation if needed.",
        "room change": "🏠 Check availability and help move the guest. Offer upgrades if no similar room is available.",
        "late checkout": "🕐 Check occupancy. If available, allow until 1–2PM. Offer storage if not possible.",
        "early check-in": "🌅 If room is ready, offer it (may include fee). Else, hold luggage and notify when ready.",
        "card terminal not working": "💳 Restart the terminal, try manual entry. If needed, take offline payment and note it.",
        "PMS system down": "📋 Use manual check-in forms. Track everything and enter data when the system is back.",
        "printer not working": "🖨️ Check paper and toner. Give handwritten receipts if needed and report the issue.",
        "special request": "🛏️ Note the request (crib, pillow, etc.) and send housekeeping. Mention charges if any.",
        "overbooking": "🚨 Apologize, arrange room at another hotel, cover costs, and offer compensation.",
        "late arrival": "🌙 Greet warmly. Check ID and reservation, and provide keys and information. 24/7 check-in is fine."
    }


    def help_response(message=None):  
        return (
            "👋 *Welcome to the Hotel Staff Assistant!*\n\n"
            "Here’s what I can help with:\n"
            "🔹 Room Availability\n"
            "🔹 Guest List\n"
            "🔹 Today’s Check-ins/Check-outs\n"
            "🔹 Guest Lookup\n"
            "🔹 Daily Summary\n\n"
            "💡 Also try common questions like:\n"
            "- *'Room not ready'* \n"
            "- *'Key not working'* \n"
            "- *'Guest complaint'* \n"
            "Type *help* anytime to see this again."
        )


    # ------------- INTENT DETECTION -------------
    def detect_intent(message, staff_faq_intents=staff_faq_intents, detect_help_request=detect_help_request, help_response=help_response):
        msg = message.lower()
        
        # Staff FAQ checks
        for keyword, response in staff_faq_intents.items():
            if keyword in msg:
                return response

        # Fallback/default or existing logic
        if detect_help_request(msg):#if "help" in message:
            return help_response()
            

        elif "available rooms" in msg or ("room" in msg):
            return "list_available_rooms"
        elif "guest list" in msg or "show guests" in msg or "guest" in msg:
            return "list_all_guests"
        return "🤔 I'm not sure how to help with that yet. Type *help* to see available options."


    # ------------- EXTRACT INFO FROM MESSAGE -------------
    def extract_room_number(message):
        match = re.search(r'\b\d{3}\b', message)
        return match.group() if match else None

    def extract_guest_name(message):
        match = re.search(r'check in ([a-zA-Z ]+) to', message.lower())
        return match.group(1).strip().title() if match else None

    # ------------- MAIN CHAT LOGIC -------------
    #need to adjust DB connection and PMS API URL


    # ------------- DATABASE QUERYING -------------
    #works
    def get_available_rooms(connect_db=connect_db):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT avail FROM room")
            rooms = [row[0] for row in cursor.fetchall()]
            conn.close()
            if rooms:
                return "rooms: " + ", ".join(rooms)
            else:
                return "No rooms."
        except Exception as e:
            return f"Error checking rooms: {str(e)}"
        
    #works
    def get_all_guests(connect_db=connect_db):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM customer")
            guests = [row[0] for row in cursor.fetchall()]
            conn.close()
            if guests:
                return "Guests currently checked in: " + ", ".join(guests)
            else:
                return "No guests found in the system."
        except Exception as e:
            return f"Error fetching guest list: {str(e)}"

    def process_staff_message(self,message,detect_help_request=detect_help_request, help_response=help_response, detect_intent=detect_intent,get_available_rooms=get_available_rooms,get_all_guests=get_all_guests):
        if detect_help_request(message):
            return help_response(message)

        intent = detect_intent(message)

        if intent == "list_available_rooms":
            return get_available_rooms()
        elif intent == "list_all_guests":
            return get_all_guests()
        return detect_intent(message)
    # ------------- TKINTER UI SETUP -------------
    def send_message(self):
        user_msg = self.user_input.get()
        if user_msg:
            self.chat_area.insert(tk.END, f"Staff: {user_msg}\n")
            bot_reply = self.process_staff_message(user_msg)
            self.chat_area.insert(tk.END, f"Bot: {bot_reply}\n\n")
            self.user_input.delete(0, tk.END)


 

if __name__ == "__main__":
    root = tk.Tk()
    chatbot = ChatbotWindow(root)
    root.mainloop()
    #root.mainloop()
