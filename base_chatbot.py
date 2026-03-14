"""Shared base class for all hotel chatbots with full PMS functionality."""

import tkinter as tk
from tkinter import scrolledtext
import mysql.connector
import datetime
from fuzzywuzzy import fuzz

# Role permissions from your original
ROLE_PERMISSIONS = {
    "Receptionist": {"mark_clean": False},
    "Housekeeper": {"mark_clean": True},
    "Manager": {"mark_clean": True}
}

class BaseChatbot(tk.Toplevel):
    """A fully-featured PMS chatbot base with all hotel operations."""

    def __init__(self, master=None, db_config=None, role='General'):
        super().__init__(master)
        self.title(f"{role} Chatbot")
        self.geometry("520x420")
        self.resizable(False, False)

        # --- config ---
        self.db_config = db_config or {}
        self.role = role
        self.conn = None
        self.cursor = None

        # --- UI ---
        self.chat_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled', height=20)
        self.chat_area.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)

        entry_frame = tk.Frame(self)
        entry_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.user_entry = tk.Entry(entry_frame)
        self.user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.user_entry.bind("<Return>", lambda e: self.on_send())

        send_btn = tk.Button(entry_frame, text="Send", width=10, command=self.on_send)
        send_btn.pack(side=tk.RIGHT)

        # Connect to DB on startup
        self._connect_db()
        
        # show help on startup
        try:
            self.bot_message(self.get_help_text())
        except Exception:
            # Allow subclasses to not implement get_help_text during incremental development
            pass

    # -------------------------
    # Database Connection (from original)
    # -------------------------
    def _connect_db(self):
        """Connect to database on initialization like original version."""
        try:
            self.conn = mysql.connector.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            self.bot_message("Hello! 👋 I'm your staff assistant. Try: 'Who is checking in today?', 'Mark room 2 as cleaned', or 'Show summary'.")
        except Exception as e:
            self.conn = None
            self.cursor = None
            self.bot_message("Warning: Could not connect to database. DB features will be disabled.\nError: " + str(e))

    def _connect(self):
        """Alternative connection method for on-demand use."""
        return mysql.connector.connect(**self.db_config)

    # -------------------------
    # Messaging helpers
    # -------------------------
    def bot_message(self, text: str):
        self._append_message("Bot", text)

    def user_message(self, text: str):
        self._append_message("You", text)

    def _append_message(self, sender: str, text: str):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{sender}: {text}\n\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    # -------------------------
    # Event handlers
    # -------------------------
    def on_send(self):
        msg = self.user_entry.get().strip()
        if not msg:
            return
        self.user_entry.delete(0, tk.END)
        self.user_message(msg)
        try:
            response = self.handle_intent(msg)
        except Exception as e:
            response = f"Error: {e}"
        self.bot_message(response)

    # -------------------------
    # Intent handling (from original with fuzzy matching)
    # -------------------------
    def handle_intent(self, text: str) -> str:
        """Default intent handling with fuzzy matching - can be overridden by subclasses."""
        msg_l = text.lower()

        # HELP command
        if msg_l in ["help", "?", "commands", "what can you do", "menu"]:
            return self.get_help_text()

        # check common intents with fuzzy matching for robustness
        if fuzz.partial_ratio("check in", msg_l) > 75 or fuzz.partial_ratio("check-in", msg_l) > 75 or "checking in" in msg_l or "checkins" in msg_l:
            return self.get_today_checkins()

        if fuzz.partial_ratio("check out", msg_l) > 75 or fuzz.partial_ratio("check-out", msg_l) > 75 or "checking out" in msg_l or "checkouts" in msg_l:
            return self.get_today_checkouts()

        if ("mark" in msg_l or "set" in msg_l) and ("clean" in msg_l or "cleaned" in msg_l):
            room_no = self.extract_number(msg_l)
            if not room_no:
                return "Which room should I mark as cleaned? Please include the room number."
            if not ROLE_PERMISSIONS.get(self.role, {}).get("mark_clean", False):
                return "You don't have permission to mark rooms as cleaned. (Switch to Housekeeper or Manager role.)"
            return self.mark_room_clean(room_no)

        if "status" in msg_l and "room" in msg_l:
            room_no = self.extract_number(msg_l)
            if not room_no:
                return "Please specify a room number to check its status."
            return self.get_room_status(room_no)

        if "summary" in msg_l or "today's summary" in msg_l or "daily summary" in msg_l:
            return self.get_daily_summary()

        if "available" in msg_l or "free room" in msg_l or "vacant" in msg_l:
            return self.get_available_rooms()

        if "guest" in msg_l or "customer" in msg_l or "tell me about" in msg_l:
            return self.get_customer_info(msg_l)

        # fallback
        return "Sorry, I didn't understand. Try: 'Who is checking in today?', 'Show summary', 'Mark room 2 as cleaned', or 'What is the status of room 2?'"

    # -------------------------
    # PMS Database Methods (from your original working version)
    # -------------------------
    @staticmethod
    def extract_number(text):
        digits = ''.join(ch for ch in text if ch.isdigit())
        return digits if digits else None

    def get_today_checkins(self):
        if not self.cursor:
            return "DB not connected."
        today = datetime.date.today().strftime("%Y-%m-%d")
        try:
            self.cursor.execute("SELECT contact, roomtype, avail, resaid, checkin FROM room WHERE checkin=%s", (today,))
            rows = self.cursor.fetchall()
            if not rows:
                return "No check-ins scheduled for today."
            lines = []
            for contact, roomtype, avail, resaid, checkin in rows:
                lines.append(f"🏨 Contact: {contact} — Type: {roomtype} — Code: {avail} — ResID: {resaid}")
            return "\n".join(lines)
        except Exception as e:
            return "Error fetching check-ins: " + str(e)

    def get_today_checkouts(self):
        if not self.cursor:
            return "DB not connected."
        today = datetime.date.today().strftime("%Y-%m-%d")
        try:
            self.cursor.execute("SELECT contact, roomtype, avail, resaid, checkout FROM room WHERE checkout=%s", (today,))
            rows = self.cursor.fetchall()
            if not rows:
                return "No check-outs scheduled for today."
            lines = []
            for contact, roomtype, avail, resaid, checkout in rows:
                lines.append(f"👋 Contact: {contact} — Type: {roomtype} — Code: {avail} — ResID: {resaid}")
            return "\n".join(lines)
        except Exception as e:
            return "Error fetching check-outs: " + str(e)

    def get_room_status(self, room_no):
        if not self.cursor:
            return "DB not connected."
        try:
            self.cursor.execute(
                "SELECT status, housekeeper_name, last_updated FROM housekeeping WHERE room_number=%s ORDER BY last_updated DESC LIMIT 1",
                (room_no,)
            )
            result = self.cursor.fetchone()
            if not result:
                return f"No housekeeping record found for room {room_no}."
            status, hk_name, last_updated = result
            ts = last_updated.strftime("%Y-%m-%d %H:%M") if hasattr(last_updated, "strftime") else str(last_updated)
            return f"Room {room_no} — {status} (last updated by {hk_name} on {ts})"
        except Exception as e:
            return "Error fetching room status: " + str(e)

    def mark_room_clean(self, room_no):
        if not self.cursor or not self.conn:
            return "DB not connected."
        try:
            now_user = self.role
            self.cursor.execute(
                "INSERT INTO housekeeping (room_number, status, housekeeper_name) VALUES (%s, 'Cleaned', %s)",
                (room_no, now_user)
            )
            self.conn.commit()
            return f"✅ Room {room_no} marked as Cleaned by {now_user}."
        except Exception as e:
            return "Error marking room cleaned: " + str(e)

    def get_available_rooms(self):
        if not self.cursor:
            return "DB not connected."
        try:
            self.cursor.execute("SELECT roomnb, roomtype, floor FROM details WHERE roomnb NOT IN (SELECT avail FROM room)")
            rows = self.cursor.fetchall()
            if not rows:
                return "No rooms currently available (or query returned none)."
            return "\n".join([f"🛏️ Room {r} — {t} (Floor {f})" for r, t, f in rows])
        except Exception as e:
            return "Error fetching available rooms: " + str(e)

    def get_customer_info(self, query):
        if not self.cursor:
            return "DB not connected."
        try:
            tokens = query.split()
            for token in tokens:
                self.cursor.execute(
                    "SELECT name, ref, mobilenumber, country, email FROM customer WHERE name LIKE %s OR mobilenumber LIKE %s",
                    (f"%{token}%", f"%{token}%")
                )
                r = self.cursor.fetchone()
                if r:
                    name, ref, mobile, country, email = r
                    return f"👤 {name} (Ref: {ref}) | Mobile: {mobile} | Country: {country} | Email: {email}"
            return "No customer found for that query."
        except Exception as e:
            return "Error searching customer: " + str(e)

    def get_daily_summary(self):
        if not self.cursor:
            return "DB not connected."
        try:
            today = datetime.date.today().strftime("%Y-%m-%d")
            self.cursor.execute("SELECT COUNT(*) FROM room WHERE checkin=%s", (today,))
            checkins = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM room WHERE checkout=%s", (today,))
            checkouts = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM housekeeping WHERE status='Cleaned'")
            cleaned = self.cursor.fetchone()[0]
            self.cursor.execute("SELECT COUNT(*) FROM housekeeping WHERE status='Not Cleaned'")
            pending = self.cursor.fetchone()[0]
            return (f"📊 Daily Summary ({today}):\n- Check-ins: {checkins}\n- Check-outs: {checkouts}\n"
                    f"- Rooms cleaned: {cleaned}\n- Pending cleaning: {pending}")
        except Exception as e:
            return "Error building summary: " + str(e)

    # -------------------------
    # Utilities
    # -------------------------
    def get_help_text(self) -> str:
        """Override this for role-specific help."""
        return (
            "Welcome to the Hotel Chatbot!\n"
            "Type your command below.\n"
            "This is the base chatbot — specific roles will have their own help menu."
        )

    def _extract_date(self, text: str, default=None):
        default = default or datetime.date.today()
        parts = text.strip().split()
        if len(parts) >= 2:
            token = parts[1]
            if token in ('today', 'now'):
                return default
            try:
                return datetime.datetime.strptime(token, "%Y-%m-%d").date()
            except ValueError:
                return default
        return default