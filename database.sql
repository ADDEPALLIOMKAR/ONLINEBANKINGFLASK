CREATE DATABASE IF NOT EXISTS online_banking;
USE online_banking;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    account_number VARCHAR(10) UNIQUE,
    balance DECIMAL(15,2) DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_acc VARCHAR(20) NOT NULL,
    receiver_acc VARCHAR(20) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO users (username, password_hash, role, account_number, balance) 
VALUES ('secret', 'secret', 'secret', 'secret', 'secret')
ON DUPLICATE KEY UPDATE username='admin';
