# simple_test.py
import tkinter as tk

class SimpleChatbot(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Simple Test Chatbot")
        self.geometry("400x300")
        
        self.chat_area = tk.Text(self, wrap=tk.WORD, height=15)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.entry = tk.Entry(self)
        self.entry.pack(padx=10, pady=10, fill=tk.X)
        self.entry.bind("<Return>", self.on_send)
        
        self.chat_area.insert(tk.END, "Simple chatbot loaded successfully!\n")
        
    def on_send(self, event):
        msg = self.entry.get()
        self.chat_area.insert(tk.END, f"You: {msg}\n")
        self.entry.delete(0, tk.END)

# Test it
root = tk.Tk()
root.withdraw()
app = SimpleChatbot(root)
print("If you see this message and a window, Tkinter is working!")
root.mainloop()