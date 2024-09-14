import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('hostel_management.db')
cursor = conn.cursor()

# Create the Tenants table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Tenants (
    tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    room_number TEXT,
    join_date DATE,
    status TEXT DEFAULT 'Active'
)
''')

# Create the Payments table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER,
    amount REAL NOT NULL,
    date DATE NOT NULL,
    status TEXT DEFAULT 'Pending',
    payment_method TEXT,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(tenant_id)
)
''')

# Create the Complaints table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Complaints (
    complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER,
    description TEXT NOT NULL,
    date DATE NOT NULL,
    status TEXT DEFAULT 'Open',
    FOREIGN KEY (tenant_id) REFERENCES Tenants(tenant_id)
)
''')

# Create the Feedback table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER,
    feedback TEXT NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(tenant_id)
)
''')

# Create the Menu table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Menu (
    menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    meal_type TEXT NOT NULL,
    items TEXT
)
''')

# Create the Users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully!")
