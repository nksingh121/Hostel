from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect('hostel_management.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route for the home page
@app.route('/')
def index():
    conn = get_db_connection()
    tenants = conn.execute('SELECT * FROM Tenants').fetchall()
    conn.close()
    return render_template('index.html', tenants=tenants)

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
