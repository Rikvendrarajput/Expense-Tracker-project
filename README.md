Let's build a comprehensive **Expense Tracker** project from scratch, including detailed steps for database setup, backend development using Flask, and frontend design using HTML and CSS. We'll also implement additional features to enhance the project's functionality. 

### **Step-by-Step Guide to Building the Expense Tracker**

---

### **1. Resetting the Database**

To ensure a clean slate, follow these steps to delete your existing database and create a new one.

#### **Delete Existing Database:**

1. **Open MySQL Workbench.**
2. Execute the following SQL command to drop your existing database:
    ```sql
    DROP DATABASE IF EXISTS rishi;
    ```

#### **Create New Database and Tables:**

Run this SQL script to set up a new database with the necessary tables:

```sql
-- Create the database
CREATE DATABASE IF NOT EXISTS rishi;

-- Use the database
USE rishi;

-- Create Users table (optional for multi-user support)
CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Create Categories table for expense categories
CREATE TABLE IF NOT EXISTS Categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL UNIQUE
);

-- Create Expenses table to store expense data
CREATE TABLE IF NOT EXISTS Expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    expense_date DATE NOT NULL,
    category_id INT NOT NULL,
    description VARCHAR(255),
    payment_method VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);

-- Insert default categories
INSERT INTO Categories (category_name) VALUES 
('Food'), ('Transport'), ('Entertainment'), ('Utilities'), ('Health'), 
('Groceries'), ('Clothing'), ('Education'), ('Rent'), ('Others');

-- Optional: Insert a default user
INSERT INTO Users (username, email, password) VALUES 
('testuser', 'test@example.com', 'password');
```

---

### **2. Project Structure**

Create a folder named **ExpenseTracker** with the following structure:

```plaintext
ExpenseTracker/
│
├── static/
│   └── styles.css  # CSS for styling
│
├── templates/
│   ├── index.html
│   ├── add_expense.html
│   ├── view_expenses.html
│   ├── update_expense.html
│   ├── navbar.html  # Optional for consistent navigation
│   └── login.html   # For user authentication
│
├── app.py           # Main Flask application
└── requirements.txt  # List of dependencies for Flask and MySQL
```

---

### **3. Backend (Flask) Setup**

#### **File: `app.py`**

This is the main backend code that handles database operations, including CRUD functionality for expenses.

```python
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
            database='rishi',  # Your MySQL database name
            user='root',       # Your MySQL username
            password='yourpassword'  # Your MySQL password
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

if

 __name__ == "__main__":
    app.run(debug=True)
```

### **4. Frontend (HTML)**

#### **File: `index.html`**

This is the homepage with navigation to add or view expenses.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Expense Tracker</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <div class="container">
        <h1 class="mt-5">Expense Tracker</h1>
        <a href="/register" class="btn btn-primary mt-3">Register</a>
        <a href="/login" class="btn btn-success mt-3">Login</a>
    </div>
</body>
</html>
```

#### **File: `login.html`**

This page allows users to log in to the application.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h2 class="mt-5">Login</h2>
        <form action="/login" method="POST" class="mt-3">
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" class="form-control" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-primary">Login</button>
        </form>
    </div>
</body>
</html>
```

#### **File: `register.html`**

This page allows new users to register.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h2 class="mt-5">Register</h2>
        <form action="/register" method="POST" class="mt-3">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" class="form-control" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" class="form-control" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-primary">Register</button>
        </form>
    </div>
</body>
</html>
```

#### **File: `add_expense.html`**

This form allows users to add an expense.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Expense</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h2 class="mt-5">Add a New Expense</h2>
        <form action="/add" method="POST" class="mt-3">
            <div class="form-group">
                <label for="amount">Amount</label>
                <input type="number" class="form-control" id="amount" name="amount" required>
            </div>
            <div class="form-group">
                <label for="date">Date</label>
                <input type="date" class="form-control" id="date" name="date" required>
            </div>
            <div class="form-group">
                <label for="category">Category</label>
                <select class="form-control" id="category" name="category" required>
                    <option value="">Select Category</option>
                    {% for category in categories %}
                        <option value="{{ category.category_id }}">{{ category.category_name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="form-group">
                <label for="custom_category">Custom Category (optional)</label>
                <input type="text" class="form-control" id="custom_category" name="custom_category">
            </div>
            <div class="form-group">
                <label for="description">Description</label>
                <input type="text" class="form-control" id="description" name="description">
            </div>
            <div class="form-group">
                <label for="payment_method">Payment Method</label>
                <input type="text" class="form-control" id="payment_method" name="payment_method">
            </div>
            <button type="submit" class="btn btn-primary">Add Expense</button>
        </form>
    </div>
</body>
</html>
```

#### **File: `view_expenses.html`**

This page displays the list of expenses.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Expenses</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h2 class="mt-5">View Expenses</h2>
        <a href="/add" class="btn btn-primary mb-3">Add New Expense</a>
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Amount</th>
                    <th>Date</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Payment Method</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for expense in expenses %}
                <tr>
                    <td>{{ expense.expense_id }}</td>
                    <td>{{ expense.amount }}</td>
                    <td>{{ expense.expense_date }}</td>
                    <td>{{ expense.category_name }}</td>
                    <td>{{ expense.description }}</td>
                    <td>{{ expense.payment_method }}</td>
                    <td>
                        <a href="/update/{{ expense.expense_id }}" class="btn btn-warning">Edit</a>
                        <a href="/delete/{{ expense.expense_id }}" class="btn btn-danger" onclick="return confirm('Are you sure you want to delete this expense?');">Delete</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
```

#### **File: `update_expense.html`**

This form allows users to update an existing expense.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Update Expense</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h2 class="mt-5">Update Expense</h2>
        <form action="/update/{{ expense.expense_id }}" method="POST" class="mt-3">
            <div class="form-group">
                <label for="amount">Amount</label>
                <input type="number" class="form-control" id="amount" name="amount" value="{{ expense.amount }}" required>
            </div>
            <div class="form-group">
                <label for="date">Date</label>
                <input type="date" class="form-control" id="date" name="date" value="{{ expense.expense_date }}" required>
            </div>
            <div class="form-group">
                <label for="category">Category</label>
                <select class="form-control" id="category" name="category" required>
                    <option value="">Select Category</option>
                    {% for category in categories %}
                        <option value="{{ category.category_id }}" {% if category.category_id == expense.category_id %}selected{% endif %}>
                            {{ category.category_name }}
                        </option>
                    {% endfor %}
                </select>
            </div>
            <div class="form-group">
                <label for="

description">Description</label>
                <input type="text" class="form-control" id="description" name="description" value="{{ expense.description }}">
            </div>
            <div class="form-group">
                <label for="payment_method">Payment Method</label>
                <input type="text" class="form-control" id="payment_method" name="payment_method" value="{{ expense.payment_method }}">
            </div>
            <button type="submit" class="btn btn-primary">Update Expense</button>
        </form>
    </div>
</body>
</html>
```

#### **File: `styles.css`**

Add some basic styles to your application.

```css
body {
    background-color: #f8f9fa;
}

.container {
    margin-top: 50px;
}

h1, h2 {
    color: #343a40;
}

.btn {
    margin-right: 10px;
}
```

### **5. Additional Features**

To enhance the utility of your Expense Tracker, consider implementing the following features:

1. **User Authentication**: Implement user registration and login, allowing multiple users to maintain their own expense records.
  
2. **Category Management**: Allow users to add, update, and delete expense categories.

3. **Expense Reports**: Generate reports summarizing expenses by category or date range.

4. **Recurring Expenses**: Allow users to set recurring expenses that automatically add to their records.

5. **Budget Tracker**: Implement a budgeting feature to help users set and track their spending limits.

6. **Export to CSV**: Allow users to export their expense data to a CSV file for external analysis.

7. **Data Visualization**: Use libraries like Chart.js to provide visual representations of expense data (pie charts, bar graphs).

8. **Notifications**: Send reminders for upcoming recurring expenses or budget limits.

9. **Responsive Design**: Ensure the web interface is mobile-friendly.

10. **Dark Mode**: Add a toggle for dark mode in the UI for better user experience at night.

### **6. Running the Application**

1. **Install Required Packages**: Create a `requirements.txt` file with the following dependencies:
   ```
   Flask
   mysql-connector-python
   Werkzeug
   ```

2. **Install the packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask Application**:
   ```bash
   python app.py
   ```

4. **Access the Application**: Open your browser and go to `http://127.0.0.1:5000/`.

### **7. Conclusion**

This setup provides a solid foundation for your Expense Tracker project. You can build upon it with additional features as mentioned above. Make sure to handle errors gracefully and implement proper security measures, especially when dealing with user data.

Feel free to ask for further enhancements or clarifications!
