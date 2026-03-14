# test_dependencies.py
try:
    import tkinter
    print("✅ tkinter OK")
except ImportError as e:
    print(f"❌ tkinter failed: {e}")

try:
    import mysql.connector
    print("✅ mysql.connector OK") 
except ImportError as e:
    print(f"❌ mysql.connector failed: {e}")

try:
    from fuzzywuzzy import fuzz
    print("✅ fuzzywuzzy OK")
except ImportError as e:
    print(f"❌ fuzzywuzzy failed: {e}")

print("Dependencies check complete.")