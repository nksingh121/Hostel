import os
import secrets
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re
import requests
import psycopg2
from menu_data import weekly_menu  # Import the weekly_menu from menu_data.py

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
    #conn = sqlite3.connect('hostel_management.db')
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
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
    
    conn = get_db_connection()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        room_number = request.form['room_number']
        join_date = request.form['join_date']

        # Server-side validation
        if not name or not email or not phone or not room_number or not join_date:
            flash('All fields are required!', 'danger')
            available_rooms = conn.execute('SELECT * FROM Rooms WHERE status = "available"').fetchall()
            return render_template('add_tenant.html', available_rooms=available_rooms)

        # Insert new tenant into the database
        conn.execute('INSERT INTO Tenants (name, email, phone, room_number, join_date) VALUES (?, ?, ?, ?, ?)',
                     (name, email, phone, room_number, join_date))

        # Update the room status to 'occupied'
        conn.execute('UPDATE Rooms SET status = "occupied" WHERE room_number = ?', (room_number,))
        conn.commit()
        conn.close()

        flash('Tenant added successfully!', 'success')
        return redirect(url_for('index'))

    # Fetch available rooms
    available_rooms = conn.execute('SELECT * FROM Rooms WHERE status = "available"').fetchall()
    conn.close()
    return render_template('add_tenant.html', available_rooms=available_rooms)



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
        new_room_number = request.form['room_number']
        join_date = request.form['join_date']
        old_room_number = tenant['room_number']  # Get the previously assigned room number

        # Server-side validation
        if not name or not email or not phone or not new_room_number or not join_date:
            flash('All fields are required!', 'danger')
            available_rooms = conn.execute('SELECT * FROM Rooms WHERE status = "available"').fetchall()
            return render_template('edit_tenant.html', tenant=tenant, available_rooms=available_rooms)

        # Update tenant details in the database
        conn.execute('UPDATE Tenants SET name = ?, email = ?, phone = ?, room_number = ?, join_date = ? WHERE tenant_id = ?',
                     (name, email, phone, new_room_number, join_date, tenant_id))

        # Update room status if room number has changed
        if new_room_number != old_room_number:
            # Set the new room to 'occupied'
            conn.execute('UPDATE Rooms SET status = "occupied" WHERE room_number = ?', (new_room_number,))
            # Set the old room to 'available'
            conn.execute('UPDATE Rooms SET status = "available" WHERE room_number = ?', (old_room_number,))
        
        conn.commit()
        conn.close()

        flash('Tenant details updated successfully!', 'success')
        return redirect(url_for('index'))

    # Fetch available rooms excluding the current room number
    available_rooms = conn.execute('SELECT * FROM Rooms WHERE status = "available" OR room_number = ?', (tenant['room_number'],)).fetchall()
    conn.close()
    return render_template('edit_tenant.html', tenant=tenant, available_rooms=available_rooms)


# Admin: Manage rent payments
@app.route('/rent_payments', methods=('GET', 'POST'))
def rent_payments():
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()

    # Retrieve filter/search parameters
    tenant_id = request.args.get('tenant_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    status = request.args.get('status', '')
    payment_method = request.args.get('payment_method', '')

    # Build the SQL query with filters
    query = '''
    SELECT Payments.*, Tenants.name as tenant_name, Tenants.room_number 
    FROM Payments 
    INNER JOIN Tenants ON Payments.tenant_id = Tenants.tenant_id 
    WHERE 1=1
    '''
    params = []

    if tenant_id:
        query += ' AND Tenants.tenant_id = ?'
        params.append(tenant_id)
    if start_date:
        query += ' AND Payments.date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND Payments.date <= ?'
        params.append(end_date)
    if status:
        query += ' AND Payments.status = ?'
        params.append(status)
    if payment_method:
        query += ' AND Payments.payment_method = ?'
        params.append(payment_method)

    payments = conn.execute(query, params).fetchall()

    # Fetch tenant information for dropdowns
    tenants = conn.execute('SELECT tenant_id, name, room_number FROM Tenants').fetchall()

    if request.method == 'POST':
        tenant_id = request.form['tenant_id']
        amount = request.form['amount']
        payment_method = request.form['payment_method']
        date = request.form['date']

        # Server-side validation
        if not tenant_id or not amount or not payment_method or not date:
            flash('All fields are required!', 'danger')
            return render_template('rent_payments.html', payments=payments, tenants=tenants)

        # Insert new payment into the database
        conn.execute('INSERT INTO Payments (tenant_id, amount, date, status, payment_method) VALUES (?, ?, ?, ?, ?)',
                     (tenant_id, amount, date, 'Paid', payment_method))
        conn.commit()
        conn.close()
        flash('Payment recorded successfully!', 'success')
        return redirect(url_for('rent_payments'))

    conn.close()
    return render_template('rent_payments.html', payments=payments, tenants=tenants)


# Admin: Delete a payment
@app.route('/delete_payment/<int:payment_id>', methods=['POST'])
def delete_payment(payment_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Check if the payment exists
    payment = conn.execute('SELECT * FROM Payments WHERE payment_id = ?', (payment_id,)).fetchone()

    if payment:
        # Delete the payment
        conn.execute('DELETE FROM Payments WHERE payment_id = ?', (payment_id,))
        conn.commit()
        flash('Payment deleted successfully!', 'success')
    else:
        flash('Payment not found!', 'danger')

    conn.close()
    return redirect(url_for('rent_payments'))



# Admin: Edit payment details
@app.route('/edit_payment/<int:payment_id>', methods=('GET', 'POST'))
def edit_payment(payment_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    payment = conn.execute('SELECT * FROM Payments WHERE payment_id = ?', (payment_id,)).fetchone()

    if request.method == 'POST':
        amount = request.form['amount']
        payment_method = request.form['payment_method']
        date = request.form['date']
        status = request.form['status']

        # Server-side validation
        if not amount or not payment_method or not date or not status:
            flash('All fields are required!', 'danger')
            return render_template('edit_payment.html', payment=payment)

        # Update payment details in the database
        conn.execute('UPDATE Payments SET amount = ?, date = ?, status = ?, payment_method = ? WHERE payment_id = ?',
                     (amount, date, status, payment_method, payment_id))
        conn.commit()
        conn.close()

        flash('Payment details updated successfully!', 'success')
        return redirect(url_for('rent_payments'))

    conn.close()
    return render_template('edit_payment.html', payment=payment)



# Admin: View and manage complaints
@app.route('/view_complaints', methods=('GET', 'POST'))
def view_complaints():
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Retrieve filter parameters
    tenant_id = request.args.get('tenant_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    status = request.args.get('status', '')

    # Build the SQL query with filters
    query = '''
    SELECT Complaints.*, Tenants.name as tenant_name, Tenants.room_number 
    FROM Complaints 
    INNER JOIN Tenants ON Complaints.tenant_id = Tenants.tenant_id 
    WHERE 1=1
    '''
    params = []

    if tenant_id:
        query += ' AND Tenants.tenant_id = ?'
        params.append(tenant_id)
    if start_date:
        query += ' AND Complaints.date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND Complaints.date <= ?'
        params.append(end_date)
    if status:
        query += ' AND Complaints.status = ?'
        params.append(status)

    complaints = conn.execute(query, params).fetchall()

    # Fetch tenant information for dropdowns
    tenants = conn.execute('SELECT tenant_id, name, room_number FROM Tenants').fetchall()

    conn.close()
    return render_template('view_complaints.html', complaints=complaints, tenants=tenants)

# Admin: Update complaint status
@app.route('/update_complaint_status/<int:complaint_id>', methods=['POST'])
def update_complaint_status(complaint_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    new_status = request.form['status']

    conn = get_db_connection()
    conn.execute('UPDATE Complaints SET status = ? WHERE complaint_id = ?', (new_status, complaint_id))
    conn.commit()
    conn.close()

    flash('Complaint status updated successfully!', 'success')
    return redirect(url_for('view_complaints'))

# Admin: Delete a complaint
@app.route('/delete_complaint/<int:complaint_id>', methods=['POST'])
def delete_complaint(complaint_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Execute deletion query
    conn.execute('DELETE FROM Complaints WHERE complaint_id = ?', (complaint_id,))
    conn.commit()
    conn.close()

    flash('Complaint deleted successfully!', 'success')
    return redirect(url_for('view_complaints'))



# Admin: Remove a tenant
@app.route('/delete_tenant/<int:tenant_id>', methods=['POST'])
def delete_tenant(tenant_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    # Fetch the tenant's details including their room number and email
    tenant = conn.execute('SELECT * FROM Tenants WHERE tenant_id = ?', (tenant_id,)).fetchone()
    
    if tenant:
        room_number = tenant['room_number']  # Get the room number of the tenant
        email = tenant['email']  # Get the email of the tenant

        # Remove tenant from the Tenants table
        conn.execute('DELETE FROM Tenants WHERE tenant_id = ?', (tenant_id,))
        
        # Remove user from the Users table using tenant's email as username
        conn.execute('DELETE FROM Users WHERE username = ?', (email,))

        # Update the room status to 'available'
        conn.execute('UPDATE Rooms SET status = "available" WHERE room_number = ?', (room_number,))
        
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

# Tenant: Log a new complaint and view complaint history
@app.route('/log_complaint', methods=['GET', 'POST'])
def log_complaint():
    if 'username' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))

    conn = get_db_connection()

    if request.method == 'POST':
        tenant_id = session['tenant_id']
        description = request.form['description']

        # Insert the new complaint into the database
        conn.execute('INSERT INTO Complaints (tenant_id, description, date, status) VALUES (?, ?, DATE("now"), ?)',
                     (tenant_id, description, 'Open'))
        conn.commit()
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('log_complaint'))

    # Fetch all complaints for the logged-in tenant
    tenant_id = session['tenant_id']
    complaints = conn.execute('SELECT * FROM Complaints WHERE tenant_id = ? ORDER BY date DESC', (tenant_id,)).fetchall()

    # Check if there is a message for the tenant from the admin's action
    if 'tenant_message' in session:
        flash(session['tenant_message'], 'info')
        session.pop('tenant_message')  # Remove the message from the session after displaying it

    conn.close()
    return render_template('/tenants/log_complaint.html', complaints=complaints)



# Tenant: Request an edit for a complaint
@app.route('/request_edit_complaint/<int:complaint_id>', methods=['POST'])
def request_edit_complaint(complaint_id):
    if 'username' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))

    tenant_id = session['tenant_id']

    # Check if the complaint belongs to the tenant
    conn = get_db_connection()
    complaint = conn.execute('SELECT * FROM Complaints WHERE complaint_id = ? AND tenant_id = ?', (complaint_id, tenant_id)).fetchone()

    if complaint:
        # Update the status to 'Edit Requested'
        conn.execute('UPDATE Complaints SET status = ? WHERE complaint_id = ?', ('Edit Requested', complaint_id))
        conn.commit()
        conn.close()
        flash('Edit request sent to the admin.', 'success')
    else:
        conn.close()
        flash('Complaint not found or does not belong to you.', 'danger')

    return redirect(url_for('log_complaint'))


# Tenant: Edit an approved complaint
@app.route('/edit_complaint/<int:complaint_id>', methods=['POST'])
def edit_complaint(complaint_id):
    if 'username' not in session or session['role'] != 'Tenant':
        return redirect(url_for('login'))

    tenant_id = session['tenant_id']
    description = request.form['description']

    conn = get_db_connection()

    # Ensure the complaint belongs to the tenant and is approved for editing
    complaint = conn.execute('SELECT * FROM Complaints WHERE complaint_id = ? AND tenant_id = ? AND status = ?', 
                             (complaint_id, tenant_id, 'Approved for Edit')).fetchone()

    if complaint:
        # Update the complaint description
        conn.execute('UPDATE Complaints SET description = ?, status = ? WHERE complaint_id = ?', 
                     (description, 'Open', complaint_id))
        conn.commit()
        flash('Complaint updated successfully!', 'success')
    else:
        flash('Complaint not found or not authorized to edit.', 'danger')

    conn.close()
    return redirect(url_for('log_complaint'))




# Admin: Approve or reject edit requests
@app.route('/admin/complaints/handle_edit_request/<int:complaint_id>', methods=['POST'])
def handle_edit_request(complaint_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    action = request.form['action']
    conn = get_db_connection()

    if action == 'approve':
        # Allow the tenant to edit the complaint
        conn.execute('UPDATE Complaints SET status = ? WHERE complaint_id = ?', ('Approved for Edit', complaint_id))
        flash('Edit request approved. Tenant can now edit the complaint.', 'success')

        # Get the tenant ID associated with this complaint
        tenant_id = conn.execute('SELECT tenant_id FROM Complaints WHERE complaint_id = ?', (complaint_id,)).fetchone()['tenant_id']
        # Set a flag in the session to show a message to the tenant
        session['tenant_message'] = f"Your edit request for complaint {complaint_id} was approved. You can now edit your complaint."

    elif action == 'reject':
        # Reject the edit request
        conn.execute('UPDATE Complaints SET status = ? WHERE complaint_id = ?', ('Open', complaint_id))
        flash('Edit request rejected.', 'danger')

        # Get the tenant ID associated with this complaint
        tenant_id = conn.execute('SELECT tenant_id FROM Complaints WHERE complaint_id = ?', (complaint_id,)).fetchone()['tenant_id']
        # Set a flag in the session to show a message to the tenant
        session['tenant_message'] = f"Your edit request for complaint {complaint_id} was declined."

    conn.commit()
    conn.close()
    return redirect(url_for('view_complaints'))





# Tenant: View the food menu
@app.route('/food_menu')
def food_menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM Menu ORDER BY date DESC').fetchall()
    conn.close()
    return render_template('tenants/food_menu.html', menu_items=menu_items)
#-----------------------------------------------------------------x-------------------------------------------------------#
# # Admin: Manage food menu
# @app.route('/menu', methods=('GET', 'POST'))
# def menu():
#     if 'username' not in session or session['role'] != 'Admin':
#         return redirect(url_for('login'))
    
#     conn = get_db_connection()
#     menu_items = conn.execute('SELECT * FROM Menu').fetchall()

#     if request.method == 'POST':
#         date = request.form['date']
#         meal_type = request.form['meal_type']
#         items = request.form['items']

#         conn.execute('INSERT INTO Menu (date, meal_type, items) VALUES (?, ?, ?)', (date, meal_type, items))
#         conn.commit()
#         conn.close()
#         flash('Menu updated successfully!', 'success')
#         return redirect(url_for('menu'))

#     conn.close()
#     return render_template('menu.html', menu_items=menu_items)

#---------------------------------------------------------------x--------------------------------------------#

# Define the weekly food menu
# weekly_menu = {
#     'Monday': ['Rice', 'Chicken Curry', 'Salad'],
#     'Tuesday': ['Chapati', 'Paneer Butter Masala', 'Dal'],
#     'Wednesday': ['Pasta', 'Garlic Bread', 'Soup'],
#     'Thursday': ['Biryani', 'Raita', 'Papad'],
#     'Friday': ['Pizza', 'French Fries', 'Coleslaw'],
#     'Saturday': ['Noodles', 'Spring Rolls', 'Manchurian'],
#     'Sunday': ['Idli', 'Sambar', 'Chutney']
# }

# Route for the tenant menu
@app.route('/tenant_menu')
def tenant_menu():
    return render_template('/tenants/tenant_menu.html', menus=weekly_menu)

# Route for the admin menu
@app.route('/admin_menu')
def admin_menu():
    return render_template('admin_menu.html', menus=weekly_menu)

# Route for editing a specific day's menu (Admin only)
@app.route('/edit_menu/<day>', methods=['GET', 'POST'])
def edit_menu(day):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get the updated meal items, split by commas
        breakfast_menu = request.form['breakfast_items'].split(',')
        lunch_menu = request.form['lunch_items'].split(',')
        dinner_menu = request.form['dinner_items'].split(',')
        
        # Strip leading/trailing spaces from each item
        breakfast_menu = [item.strip() for item in breakfast_menu]
        lunch_menu = [item.strip() for item in lunch_menu]
        dinner_menu = [item.strip() for item in dinner_menu]
        
        # Update the weekly menu for the selected day
        weekly_menu[day] = {
            'Breakfast': breakfast_menu,
            'Lunch': lunch_menu,
            'Dinner': dinner_menu
        }
        
        flash(f'Menu for {day} updated successfully!', 'success')
        return redirect(url_for('admin_menu'))

    return render_template('edit_menu.html', day=day, menu=weekly_menu[day])




# User Registration
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # role = request.form['role']
        role = 'Tenant'
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

#Promote other user for admin
@app.route('/promote_user/<int:user_id>', methods=['POST'])
def promote_user(user_id):
    # Check if the current user is an admin
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    # Promote the user to admin
    conn = get_db_connection()
    conn.execute('UPDATE Users SET role = ? WHERE user_id = ?', ('Admin', user_id))
    conn.commit()
    conn.close()

    flash('User promoted to admin!', 'success')
    return redirect(url_for('admin_dashboard'))

#remove user by admins
@app.route('/remove_user/<int:user_id>', methods=['POST'])
def remove_user(user_id):
    # Check if the current user is an admin
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    # Ensure the admin cannot delete themselves
    if user_id == session.get('user_id'):
        flash("You cannot remove your own account!", 'danger')
        return redirect(url_for('admin_dashboard'))

    # Remove the user from the database
    conn = get_db_connection()
    conn.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    flash('User removed successfully!', 'success')
    return redirect(url_for('admin_dashboard'))



#admin dashboard for promoting/removing users
@app.route('/admin_dashboard')
def admin_dashboard():
    # Check if the current user is an admin
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    # Fetch all users from the database
    conn = get_db_connection()
    users = conn.execute('SELECT user_id, username, role FROM Users').fetchall()
    conn.close()

    return render_template('admin_dashboard.html', users=users)




# Tenant and Admin login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            # Store common session details for both roles
            session['username'] = user['username']
            session['role'] = user['role']
            
            if user['role'] == 'Tenant':
                # Additional step for Tenant: fetch and store tenant_id
                conn = get_db_connection()
                tenant = conn.execute('SELECT tenant_id FROM Tenants WHERE email = ?', (username,)).fetchone()
                conn.close()

                if tenant:
                    session['tenant_id'] = tenant['tenant_id']
            
            # Flash a login success message only if the query parameter 'show_login_message' is set
            if request.args.get('show_login_message') == 'true':
                flash('Login successful!', 'success')
                
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')



# User Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)