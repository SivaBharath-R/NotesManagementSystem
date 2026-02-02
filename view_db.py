import sqlite3

db = sqlite3.connect("database.db")
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Show all users
print("---- USERS ----")
cursor.execute("SELECT * FROM user1")
for row in cursor.fetchall():
    print(dict(row))

# Show all notes
print("\n---- NOTES ----")
cursor.execute("SELECT * FROM notes")
for row in cursor.fetchall():
    print(dict(row))

# Show contact messages
print("\n---- CONTACT MESSAGES ----")
cursor.execute("SELECT * FROM contact_messages")
for row in cursor.fetchall():
    print(dict(row))

db.close()
