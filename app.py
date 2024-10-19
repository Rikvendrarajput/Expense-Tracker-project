from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For flashing messages

# Function to connect to MySQL
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='ExpenseTracker',  # Your MySQL database name
            user='root',       # Your MySQL username
            password='12345'  # Your MySQL password
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

# Route: Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Route: User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, password))
        connection.commit()
        cursor.close()
        connection.close()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Route: User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            flash("Login successful!", "success")
            return redirect(url_for('view_expenses'))
        else:
            flash("Invalid email or password.", "danger")

    return render_template('login.html')

# Route: Add Expense
@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch existing categories
    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

    if request.method == 'POST':
        user_id = session['user_id']
        amount = request.form['amount']
        date = request.form['date']
        category = request.form['category']
        custom_category = request.form.get('custom_category', None)
        description = request.form['description']
        payment_method = request.form['payment_method']

        # Handle custom category
        if custom_category:
            cursor.execute("INSERT INTO Categories (category_name) VALUES (%s)", (custom_category,))
            connection.commit()
            category = cursor.lastrowid  # Use the new category ID

        # Insert expense into the database
        query = """
        INSERT INTO Expenses (user_id, amount, expense_date, category_id, description, payment_method)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, amount, date, category, description, payment_method))
        connection.commit()
        cursor.close()
        connection.close()
        flash("Expense added successfully!", "success")
        return redirect(url_for('view_expenses'))

    return render_template('add_expense.html', categories=categories)

# Route: View Expenses
@app.route('/expenses')
def view_expenses():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT Expenses.expense_id, Expenses.amount, Expenses.expense_date, 
               Categories.category_name, Expenses.description, Expenses.payment_method
        FROM Expenses
        JOIN Categories ON Expenses.category_id = Categories.category_id
        WHERE Expenses.user_id = %s
        ORDER BY expense_date DESC
        """
        cursor.execute(query, (session['user_id'],))
        expenses = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('view_expenses.html', expenses=expenses)
    return "Error connecting to database."

# Route: Update Expense
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_expense(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch existing categories
    cursor.execute("SELECT * FROM Categories")
    categories = cursor.fetchall()

    if request.method == 'POST':
        amount = request.form['amount']
        date = request.form['date']
        category = request.form['category']
        description = request.form['description']
        payment_method = request.form['payment_method']

        # Update expense in the database
        query = """
        UPDATE Expenses 
        SET amount = %s, expense_date = %s, category_id = %s, 
            description = %s, payment_method = %s 
        WHERE expense_id = %s
        """
        cursor.execute(query, (amount, date, category, description, payment_method, id))
        connection.commit()
        cursor.close()
        connection.close()
        flash("Expense updated successfully!", "success")
        return redirect(url_for('view_expenses'))

    # Get current expense details
    cursor.execute("SELECT * FROM Expenses WHERE expense_id = %s", (id,))
    expense = cursor.fetchone()
    cursor.close()
    connection.close()
    return render_template('update_expense.html', expense=expense, categories=categories)

# Route: Delete Expense
@app.route('/delete/<int:id>')
def delete_expense(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = "DELETE FROM Expenses WHERE expense_id = %s"
        cursor.execute(query, (id,))
        connection.commit()
        cursor.close()
        connection.close()
        flash("Expense deleted successfully!", "success")
    return redirect(url_for('view_expenses'))

# Route: Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
