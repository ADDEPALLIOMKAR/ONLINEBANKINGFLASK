from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import mysql.connector
import bcrypt
import random

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_session'

# Database configuration (adjust based on your local WAMP/XAMPP/MySQL config)
db_config = {
    'host': 'localhost',
    'user': 'secret', 
    'password': 'secret', 
    'database': 'secret'
}

def get_db_connection():
    """Helper to get a database connection."""
    return mysql.connector.connect(**db_config)


# VIEW ROUTES


@app.route('/')
def index():
    """Redirect to dashboard if logged in, else login page."""
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('customer_dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    return render_template('admin_dashboard.html')

@app.route('/customer')
def customer_dashboard():
    if session.get('role') != 'customer':
        return redirect(url_for('login_page'))
    return render_template('customer_dashboard.html')

# ==============================
# AUTHENTICATION API ROUTES
# ==============================

@app.route('/login', methods=['POST'])
def login():
    """Handle login via JSON request."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    # Verify user exists and check password against bcrypt hash
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['account_number'] = user['account_number']
        return jsonify({'success': True, 'role': user['role']})
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    """Clear session data to logout."""
    session.clear()
    return jsonify({'success': True})

# ==============================
# ADMIN API ROUTES
# ==============================

@app.route('/admin/create_user', methods=['POST'])
def create_customer():
    """Create a new customer user (Admin only)."""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.json
    username = data.get('username')
    password = data.get('password')
    initial_balance = float(data.get('initial_balance', 0))
    
    # Hash password with bcrypt
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Auto-generate a unique 6-digit account number limit collision checking logic for simplicity
    account_number = str(random.randint(100000, 999999))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO users (username, password_hash, role, account_number, balance) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (username, password_hash, 'customer', account_number, initial_balance))
        conn.commit()
        return jsonify({'success': True, 'message': 'User created successfully!', 'account_number': account_number})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': 'Database error or username already exists.'}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/users', methods=['GET'])
def get_users():
    """View list of all customers (Admin only)."""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, account_number, balance FROM users WHERE role = 'customer'")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(users)

@app.route('/admin/deposit', methods=['POST'])
def deposit():
    """Deposit money to any user account (Admin only)."""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.json
    account_number = data.get('account_number')
    amount = float(data.get('amount', 0))
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Deposit amount must be greater than 0.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Increase user balance
        cursor.execute("UPDATE users SET balance = balance + %s WHERE account_number = %s AND role = 'customer'", (amount, account_number))
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'Customer account not found.'}), 404
            
        # Record the transaction
        cursor.execute("INSERT INTO transactions (sender_acc, receiver_acc, amount) VALUES (%s, %s, %s)",
                       ('ADMIN', account_number, amount))
        conn.commit()
        return jsonify({'success': True, 'message': 'Deposit successful!'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/transactions', methods=['GET'])
def get_all_transactions():
    """View all transactions across the platform (Admin only)."""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(transactions)

# ==============================
# CUSTOMER API ROUTES
# ==============================

@app.route('/user/balance', methods=['GET'])
def get_balance():
    """Get the current customer's balance."""
    if session.get('role') != 'customer':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT balance FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        return jsonify({'success': True, 'balance': user['balance']})
    return jsonify({'success': False, 'message': 'User not found'}), 404

@app.route('/user/transfer', methods=['POST'])
def transfer_money():
    """Transfer money to another account (Customer only)."""
    if session.get('role') != 'customer':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.json
    receiver_acc = data.get('receiver_acc')
    amount = float(data.get('amount', 0))
    sender_acc = session.get('account_number')
    
    # Basic validation
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Amount must be greater than zero.'}), 400
    if sender_acc == receiver_acc:
        return jsonify({'success': False, 'message': 'Cannot transfer to your own account.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check sender's balance (no overdraft)
        cursor.execute("SELECT balance FROM users WHERE account_number = %s", (sender_acc,))
        sender = cursor.fetchone()
        if not sender or sender['balance'] < amount:
            return jsonify({'success': False, 'message': 'Insufficient funds.'}), 400
            
        # Check receiver exists
        cursor.execute("SELECT id FROM users WHERE account_number = %s", (receiver_acc,))
        receiver = cursor.fetchone()
        if not receiver:
            return jsonify({'success': False, 'message': 'Receiver account not found.'}), 404
            
        # Perform the transfer (update balances)
        cursor.execute("UPDATE users SET balance = balance - %s WHERE account_number = %s", (amount, sender_acc))
        cursor.execute("UPDATE users SET balance = balance + %s WHERE account_number = %s", (amount, receiver_acc))
        
        # Log the transaction
        cursor.execute("INSERT INTO transactions (sender_acc, receiver_acc, amount) VALUES (%s, %s, %s)",
                       (sender_acc, receiver_acc, amount))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Transfer completed successfully!'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/user/history', methods=['GET'])
def get_history():
    """Get the current customer's transaction history."""
    if session.get('role') != 'customer':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    account_number = session.get('account_number')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM transactions WHERE sender_acc = %s OR receiver_acc = %s ORDER BY timestamp DESC", 
        (account_number, account_number)
    )
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
