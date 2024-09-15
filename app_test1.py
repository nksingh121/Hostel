import os
import secrets
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re
import requests

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set the secret key: try to get from the environment, or generate a new one
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

# Use environment variable for reCAPTCHA keys
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')
RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY')

# Print statements to check if the keys are loaded correctly
print("FLASK_SECRET_KEY:", app.secret_key)
print("RECAPTCHA_SECRET_KEY:", RECAPTCHA_SECRET_KEY)
print("RECAPTCHA_SITE_KEY:", RECAPTCHA_SITE_KEY)

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
    
    # If the logged-in user is a tenant, redirect to their profile page
    if session['role'] == 'Tenant':
        return redirect(url_for('tenant_profile'))
    
    try:
    # For admin, show all tenants
        conn = get_db_connection()
        tenants = conn.execute('SELECT * FROM Tenants').fetchall()
        conn.close()
    except Exception as e:
        flash('An error occurred while fetching tenant data. Please try again.', 'danger')
        return render_template('index.html', tenants=[])
    return render_template('index.html', tenants=tenants)
    

# Admin: Add a new tenant
@app.route('/add_tenant', methods=('GET', 'POST'))
def add_tenant():
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
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
        flash('Tenant added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_tenant.html')

# Admin: Edit tenant details
@app.route('/edit_tenant/<int:tenant_id>', methods=('GET', 'POST'))
def edit_tenant(tenant_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
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
        flash('Tenant details updated successfully!', 'success')
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_tenant.html', tenant=tenant)

# Admin: Manage rent payments
@app.route('/rent_payments', methods=('GET', 'POST'))
def rent_payments():
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
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
        flash('Payment recorded successfully!', 'success')
        return redirect(url_for('rent_payments'))

    conn.close()
    return render_template('rent_payments.html', payments=payments)

# Admin: Log complaints
@app.route('/complaints', methods=('GET', 'POST'))
def complaints():
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
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
        flash('Complaint logged successfully!', 'success')
        return redirect(url_for('complaints'))

    conn.close()
    return render_template('complaints.html', complaints=complaints)

# Admin: Manage food menu
@app.route('/menu', methods=('GET', 'POST'))
def menu():
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM Menu').fetchall()

    if request.method == 'POST':
        date = request.form['date']
        meal_type = request.form['meal_type']
        items = request.form['items']

        conn.execute('INSERT INTO Menu (date, meal_type, items) VALUES (?, ?, ?)', (date, meal_type, items))
        conn.commit()
        conn.close()
        flash('Menu updated successfully!', 'success')
        return redirect(url_for('menu'))

    conn.close()
    return render_template('menu.html', menu_items=menu_items)

# Admin: Remove a tenant
@app.route('/delete_tenant/<int:tenant_id>', methods=['POST'])
def delete_tenant(tenant_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    # Fetch the tenant's email to remove them from the Users table
    tenant = conn.execute('SELECT * FROM Tenants WHERE tenant_id = ?', (tenant_id,)).fetchone()
    
    if tenant:
        # Remove tenant from the Tenants table
        conn.execute('DELETE FROM Tenants WHERE tenant_id = ?', (tenant_id,))
        # Remove user from the Users table using tenant's email as username
        conn.execute('DELETE FROM Users WHERE username = ?', (tenant['email'],))
        conn.commit()
        flash('Tenant and associated user account removed successfully!', 'success')
    else:
        flash('Tenant not found!', 'danger')

    conn.close()
    return redirect(url_for('index'))


# Tenant: View profile and rent history
@app.route('/profile')
def tenant_profile():
    if 'username' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    # Fetch tenant's details based on the logged-in username
    conn = get_db_connection()
    tenant = conn.execute('SELECT * FROM Tenants WHERE email = ?', (session['username'],)).fetchone()
    rent_history = conn.execute('SELECT * FROM Payments WHERE tenant_id = ?', (tenant['tenant_id'],)).fetchall()
    conn.close()
    return render_template('tenants/tenant_profile.html', tenant=tenant, rent_history=rent_history)

# Tenant: Log a complaint
@app.route('/log_complaint', methods=('GET', 'POST'))
def log_complaint():
    if 'username' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    tenant = conn.execute('SELECT * FROM Tenants WHERE email = ?', (session['username'],)).fetchone()

    if request.method == 'POST':
        description = request.form['description']
        date = request.form['date']

        conn.execute('INSERT INTO Complaints (tenant_id, description, date, status) VALUES (?, ?, ?, ?)',
                     (tenant['tenant_id'], description, date, 'Open'))
        conn.commit()
        conn.close()
        flash('Complaint logged successfully!', 'success')
        return redirect(url_for('log_complaint'))

    complaints = conn.execute('SELECT * FROM Complaints WHERE tenant_id = ?', (tenant['tenant_id'],)).fetchall()
    conn.close()
    return render_template('tenants/log_complaint.html', complaints=complaints)

# Tenant: View the food menu
@app.route('/food_menu')
def food_menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM Menu ORDER BY date DESC').fetchall()
    conn.close()
    return render_template('tenants/food_menu.html', menu_items=menu_items)

# User Registration
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        recaptcha_response = request.form.get('g-recaptcha-response')

        # Check if reCAPTCHA response is present
        if not recaptcha_response:
            flash('Please complete the reCAPTCHA verification.', 'danger')
            return render_template('register.html', site_key=RECAPTCHA_SITE_KEY)

        # Verify reCAPTCHA
        recaptcha_url = 'https://www.google.com/recaptcha/api/siteverify'
        recaptcha_payload = {'secret': RECAPTCHA_SECRET_KEY, 'response': recaptcha_response}
        recaptcha_request = requests.post(recaptcha_url, data=recaptcha_payload)
        recaptcha_result = recaptcha_request.json()

        if not recaptcha_result.get('success'):
            flash('reCAPTCHA verification failed. Please try again.', 'danger')
            return render_template('register.html', site_key=RECAPTCHA_SITE_KEY)

        # Server-side email validation using regex
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, username):
            flash('Invalid email format. Please enter a valid email address.', 'danger')
            return render_template('register.html', site_key=RECAPTCHA_SITE_KEY)

        # Server-side password strength validation
        password_regex = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@#$%^&+=!]).{8,}$'
        if not re.match(password_regex, password):
            flash('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character.', 'danger')
            return render_template('register.html', site_key=RECAPTCHA_SITE_KEY)

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

    return render_template('register.html', site_key=RECAPTCHA_SITE_KEY)



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

if __name__ == '__main__':
    app.run(debug=True)