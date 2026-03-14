# chat.py
import tkinter as tk
from tkinter import ttk
from datetime import datetime, date
import mysql.connector
from fuzzywuzzy import fuzz

# -------- CONFIG: change DB creds here ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "adm",
    "password": "&azertyt",   # <<< set your MySQL password
    "database": "management"
}
# ------------------------------------------------

ROLE_PERMISSIONS = {
    "Receptionist": {"mark_clean": False},
    "Housekeeper": {"mark_clean": True},
    "Manager": {"mark_clean": True}
}


class ChatbotWindow:
    def __init__(self, parent):
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title("Staff Chatbot Assistant")
        self.win.geometry("680x560+350+70")
        self.win.resizable(False, False)

        # Top: Role selector + welcome
        top_frame = tk.Frame(self.win)
        top_frame.pack(fill="x", padx=10, pady=(8, 0))

        tk.Label(top_frame, text="Role:", font=("Segoe UI", 10)).pack(side="left")
        self.role_var = tk.StringVar(value="Receptionist")
        role_menu = ttk.Combobox(top_frame, textvariable=self.role_var, state="readonly",
                                 values=["Receptionist", "Housekeeper", "Manager"], width=14)
        role_menu.pack(side="left", padx=(6, 10))
        role_menu.bind("<<ComboboxSelected>>", lambda e: None)

        self.status_label = tk.Label(top_frame, text="Connected", fg="green", font=("Segoe UI", 9))
        self.status_label.pack(side="right")

        # Middle: scrollable chat area (Canvas + inner frame)
        chat_frame = tk.Frame(self.win, bd=1, relief="sunken")
        chat_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(chat_frame, bg="#F5F7FA", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(chat_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # container frame inside canvas
        self.messages_container = tk.Frame(self.canvas, bg="#F5F7FA")
        self.canvas.create_window((0, 0), window=self.messages_container, anchor="nw")
        self.messages_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Bottom: entry + send button
        bottom_frame = tk.Frame(self.win)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(bottom_frame, textvariable=self.entry_var, font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.on_send())

        send_btn = tk.Button(bottom_frame, text="Send", width=12, command=self.on_send, bg="#0B57A4", fg="white")
        send_btn.pack(side="right")

        # Connect to DB (safe try/except)
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            self.bot_message("Hello! 👋 I'm your staff assistant. Try: 'Who is checking in today?', 'Mark room 2 as cleaned', or 'Show summary'.")
        except Exception as e:
            self.conn = None
            self.cursor = None
            self.status_label.config(text="DB disconnected", fg="red")
            self.bot_message("Warning: Could not connect to database. DB features will be disabled.\nError: " + str(e))

    # -------- UI helpers (message bubbles) --------
    def add_bubble(self, text, from_bot=True):
        # bubble container row
        row = tk.Frame(self.messages_container, bg="#F5F7FA")
        # timestamp
        ts = datetime.now().strftime("%H:%M")
        if from_bot:
            # left aligned
            bubble = tk.Label(row, text=text, justify="left", anchor="w",
                              font=("Segoe UI", 10), bd=0, wraplength=420, padx=10, pady=6,
                              bg="#E6F0FF", fg="#0B2242", relief="solid", borderwidth=1)
            bubble.pack(side="left", anchor="w", padx=8, pady=6)
            tk.Label(row, text=f" {ts}", font=("Segoe UI", 8), bg="#F5F7FA", fg="#606060").pack(side="left", anchor="s")
        else:
            # right aligned
            bubble = tk.Label(row, text=text, justify="left", anchor="e",
                              font=("Segoe UI", 10), bd=0, wraplength=420, padx=10, pady=6,
                              bg="#F0F0F0", fg="#111111", relief="solid", borderwidth=1)
            bubble.pack(side="right", anchor="e", padx=8, pady=6)
            tk.Label(row, text=f"{ts} ", font=("Segoe UI", 8), bg="#F5F7FA", fg="#606060").pack(side="right", anchor="s")

        row.pack(fill="x", anchor="w" if from_bot else "e")
        # auto-scroll
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def bot_message(self, text):
        # split long lines for readability
        for chunk in text.split("\n"):
            self.add_bubble(chunk, from_bot=True)

    def staff_message(self, text):
        self.add_bubble(text, from_bot=False)

    # -------- Input handling --------
    def on_send(self):
        msg = self.entry_var.get().strip()
        if not msg:
            return
        self.staff_message(msg)
        self.entry_var.set("")
        # handle intent
        self.handle_intent(msg)

    # -------- Intent detection & permission checks --------
    def handle_intent(self, msg):
        msg_l = msg.lower()

            # HELP command
        if msg_l in ["help", "?", "commands", "what can you do", "menu"]:
            self.bot_message(self.get_help_text())
            return


        # check common intents with fuzzy matching for robustness
        if fuzz.partial_ratio("check in", msg_l) > 75 or fuzz.partial_ratio("check-in", msg_l) > 75 or "checking in" in msg_l or "checkins" in msg_l:
            self.bot_message(self.get_today_checkins())
            return

        if fuzz.partial_ratio("check out", msg_l) > 75 or fuzz.partial_ratio("check-out", msg_l) > 75 or "checking out" in msg_l or "checkouts" in msg_l:
            self.bot_message(self.get_today_checkouts())
            return

        if ("mark" in msg_l or "set" in msg_l) and ("clean" in msg_l or "cleaned" in msg_l):
            room_no = self.extract_number(msg_l)
            if not room_no:
                self.bot_message("Which room should I mark as cleaned? Please include the room number.")
                return
            if not ROLE_PERMISSIONS[self.role_var.get()]["mark_clean"]:
                self.bot_message("You don't have permission to mark rooms as cleaned. (Switch to Housekeeper or Manager role.)")
                return
            self.bot_message(self.mark_room_clean(room_no))
            return

        if "status" in msg_l and "room" in msg_l:
            room_no = self.extract_number(msg_l)
            if not room_no:
                self.bot_message("Please specify a room number to check its status.")
                return
            self.bot_message(self.get_room_status(room_no))
            return

        if "summary" in msg_l or "today's summary" in msg_l or "daily summary" in msg_l:
            self.bot_message(self.get_daily_summary())
            return

        if "available" in msg_l or "free room" in msg_l or "vacant" in msg_l:
            self.bot_message(self.get_available_rooms())
            return

        if "guest" in msg_l or "customer" in msg_l or "tell me about" in msg_l:
            self.bot_message(self.get_customer_info(msg_l))
            return

        # fallback
        self.bot_message("Sorry, I didn't understand. Try: 'Who is checking in today?', 'Show summary', 'Mark room 2 as cleaned', or 'What is the status of room 2?'")

    # -------- Utilities --------
    @staticmethod
    def extract_number(text):
        digits = ''.join(ch for ch in text if ch.isdigit())
        return digits if digits else None

    # -------- PMS-aware DB functions --------
    def get_today_checkins(self):
        if not self.cursor:
            return "DB not connected."
        today = date.today().strftime("%Y-%m-%d")
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
        today = date.today().strftime("%Y-%m-%d")
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
            # last_updated could be datetime or string depending on connector config
            ts = last_updated.strftime("%Y-%m-%d %H:%M") if hasattr(last_updated, "strftime") else str(last_updated)
            return f"Room {room_no} — {status} (last updated by {hk_name} on {ts})"
        except Exception as e:
            return "Error fetching room status: " + str(e)

    def mark_room_clean(self, room_no):
        if not self.cursor or not self.conn:
            return "DB not connected."
        try:
            now_user = self.role_var.get()
            # Insert a housekeeping row (history)
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
            # details.roomnb is master list; room.avail holds codes for reserved rooms (not a perfect design but matches your dump)
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
            # search by name fragment or mobile fragment
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
            today = date.today().strftime("%Y-%m-%d")
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
        
    def get_help_text(self):
        return (
            "🧭 Here are a few things I can do:\n"
            "1️⃣  Show who is checking in today — try 'Who is checking in today?'\n"
            "2️⃣  Show who is checking out today — try 'Who is checking out today?'\n"
            "3️⃣  Mark a room as cleaned — 'Mark room 202 as cleaned'\n"
            "4️⃣  Check a room’s housekeeping status — 'Status of room 305'\n"
            "5️⃣  Show available rooms — 'Which rooms are available?'\n"
            "6️⃣  Show today’s summary — 'Show daily summary'\n"
            "7️⃣  Find a customer — 'Tell me about John'\n\n"
            "💡 Type 'help' anytime to see this list again."
        )



# For quick manual testing the module
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # hide main window
    ChatbotWindow(root)
    root.mainloop()
