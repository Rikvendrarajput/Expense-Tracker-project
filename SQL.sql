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
