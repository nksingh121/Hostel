import os
import secrets
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set the secret key: try to get from the environment, or generate a new one
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect('hostel_management.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route for the home page
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        tenants = conn.execute('SELECT * FROM Tenants').fetchall()
        conn.close()
    except Exception as e:
        flash('An error occurred while fetching tenant data. Please try again.', 'danger')
        return render_template('index.html', tenants=[])
    return render_template('index.html', tenants=tenants)

# User Registration
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)',
                         (username, password_hash, role))
            conn.commit()
            conn.close()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username already exists. Please choose a different one.', 'danger')

    return render_template('register.html')

# User Login
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

# User Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Route for adding a new tenant
@app.route('/add_tenant', methods=('GET', 'POST'))
def add_tenant():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        room_number = request.form['room_number']
        join_date = request.form['join_date']

        conn = get_db_connection()
        conn.execute('INSERT INTO Tenants (name, email, phone, room_number, join_date) VALUES (?, ?, ?, ?, ?)',
                     (name, email, phone, room_number, join_date))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add_tenant.html')

# Route for editing a tenant
@app.route('/edit_tenant/<int:tenant_id>', methods=('GET', 'POST'))
def edit_tenant(tenant_id):
    conn = get_db_connection()
    tenant = conn.execute('SELECT * FROM Tenants WHERE tenant_id = ?', (tenant_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        room_number = request.form['room_number']
        status = request.form['status']

        conn.execute('UPDATE Tenants SET name = ?, email = ?, phone = ?, room_number = ?, status = ? WHERE tenant_id = ?',
                     (name, email, phone, room_number, status, tenant_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_tenant.html', tenant=tenant)

# Route for managing rent payments
@app.route('/rent_payments', methods=('GET', 'POST'))
def rent_payments():
    conn = get_db_connection()
    payments = conn.execute('SELECT * FROM Payments').fetchall()

    if request.method == 'POST':
        tenant_id = request.form['tenant_id']
        amount = request.form['amount']
        payment_method = request.form['payment_method']
        date = request.form['date']

        conn.execute('INSERT INTO Payments (tenant_id, amount, date, status, payment_method) VALUES (?, ?, ?, ?, ?)',
                     (tenant_id, amount, date, 'Paid', payment_method))
        conn.commit()
        conn.close()
        return redirect(url_for('rent_payments'))

    conn.close()
    return render_template('rent_payments.html', payments=payments)

# Route for logging complaints
@app.route('/complaints', methods=('GET', 'POST'))
def complaints():
    conn = get_db_connection()
    complaints = conn.execute('SELECT * FROM Complaints').fetchall()

    if request.method == 'POST':
        tenant_id = request.form['tenant_id']
        description = request.form['description']
        date = request.form['date']

        conn.execute('INSERT INTO Complaints (tenant_id, description, date, status) VALUES (?, ?, ?, ?)',
                     (tenant_id, description, date, 'Open'))
        conn.commit()
        conn.close()
        return redirect(url_for('complaints'))

    conn.close()
    return render_template('complaints.html', complaints=complaints)

# Route for managing the food menu
@app.route('/menu', methods=('GET', 'POST'))
def menu():
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM Menu').fetchall()

    if request.method == 'POST':
        date = request.form['date']
        meal_type = request.form['meal_type']
        items = request.form['items']

        conn.execute('INSERT INTO Menu (date, meal_type, items) VALUES (?, ?, ?)', (date, meal_type, items))
        conn.commit()
        conn.close()
        return redirect(url_for('menu'))

    conn.close()
    return render_template('menu.html', menu_items=menu_items)

if __name__ == '__main__':
    app.run(debug=True)
