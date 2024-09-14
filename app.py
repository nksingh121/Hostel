from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('hostel_management.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    tenants = conn.execute('SELECT * FROM Tenants').fetchall()
    conn.close()
    return render_template('index.html', tenants=tenants)

if __name__ == '__main__':
    app.run(debug=True)
