import sqlite3
import os

# Auto-detect Azure vs local environment
# WEBSITE_INSTANCE_ID is set automatically by Azure App Service
if os.environ.get("WEBSITE_INSTANCE_ID"):
    DB_NAME = "/home/chat_history.db"  # Azure persistent storage
else:
    DB_NAME = "chat_history.db"        # Local development

def init_db():
    """Initializes the SQLite database to store chat messages."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_data TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role, content):
    """Saves a single message to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def get_all_messages():
    """Retrieves all chat messages in chronological order."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM messages ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        messages.append({"role": row[0], "content": row[1]})
    return messages

def clear_history():
    """Clears all chat history (optional, useful for testing or reset)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

def save_user_profile(profile_json: str):
    """Saves the extracted career profile, replacing any existing one."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_profile")
    cursor.execute("INSERT INTO user_profile (profile_data) VALUES (?)", (profile_json,))
    conn.commit()
    conn.close()

def get_user_profile():
    """Retrieves the stored user profile."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT profile_data FROM user_profile ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return None
