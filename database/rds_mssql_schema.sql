-- RDS MSSQL Schema - Transactional Database
-- This is the source of truth for financial transactions

-- Users table
CREATE TABLE users (
    user_id INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(100) NOT NULL UNIQUE,
    email NVARCHAR(255) NOT NULL UNIQUE,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- Accounts table
CREATE TABLE accounts (
    account_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    account_name NVARCHAR(100) NOT NULL,
    account_type NVARCHAR(50) NOT NULL, -- 'checking', 'savings', 'credit', 'investment'
    balance DECIMAL(18,2) DEFAULT 0.00,
    currency NVARCHAR(3) DEFAULT 'USD',
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Categories table
CREATE TABLE categories (
    category_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT,
    category_name NVARCHAR(100) NOT NULL,
    category_type NVARCHAR(20) NOT NULL, -- 'income', 'expense'
    parent_category_id INT NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
);

-- Transactions table (main transactional data)
CREATE TABLE transactions (
    transaction_id BIGINT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    account_id INT NOT NULL,
    category_id INT,
    transaction_date DATE NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    transaction_type NVARCHAR(20) NOT NULL, -- 'income', 'expense', 'transfer'
    description NVARCHAR(500),
    merchant_name NVARCHAR(200),
    payment_method NVARCHAR(50), -- 'cash', 'card', 'bank_transfer', 'check'
    tags NVARCHAR(500), -- comma-separated tags
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- Budgets table
CREATE TABLE budgets (
    budget_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    category_id INT,
    budget_amount DECIMAL(18,2) NOT NULL,
    budget_period NVARCHAR(20) NOT NULL, -- 'monthly', 'yearly', 'weekly'
    start_date DATE NOT NULL,
    end_date DATE,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- Indexes for performance
CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_date);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_accounts_user ON accounts(user_id);

-- Sample data insertion procedures
GO

CREATE PROCEDURE sp_insert_sample_transactions
    @user_id INT,
    @num_transactions INT = 100
AS
BEGIN
    DECLARE @i INT = 1;
    DECLARE @account_id INT;
    DECLARE @category_id INT;
    DECLARE @amount DECIMAL(18,2);
    DECLARE @trans_type NVARCHAR(20);
    DECLARE @trans_date DATE;
    
    SELECT TOP 1 @account_id = account_id FROM accounts WHERE user_id = @user_id;
    
    WHILE @i <= @num_transactions
    BEGIN
        SET @trans_date = DATEADD(DAY, -RAND() * 90, GETDATE());
        SET @amount = CAST(RAND() * 1000 + 10 AS DECIMAL(18,2));
        SET @trans_type = CASE WHEN RAND() > 0.7 THEN 'income' ELSE 'expense' END;
        
        SELECT TOP 1 @category_id = category_id 
        FROM categories 
        WHERE user_id = @user_id AND category_type = @trans_type
        ORDER BY NEWID();
        
        INSERT INTO transactions (user_id, account_id, category_id, transaction_date, amount, transaction_type, description)
        VALUES (@user_id, @account_id, @category_id, @trans_date, @amount, @trans_type, 'Sample transaction ' + CAST(@i AS NVARCHAR));
        
        SET @i = @i + 1;
    END
END
GO


