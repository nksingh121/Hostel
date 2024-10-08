BEGIN TRANSACTION;

-- Create Tenants Table
CREATE TABLE Tenants (
    tenant_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    room_number TEXT,
    join_date DATE,
    status TEXT DEFAULT 'Active'
);

-- Insert into Tenants
INSERT INTO Tenants VALUES(DEFAULT,'Nisikanta Singh','abc@gmail.com','08670479791','101','2024-09-01','Active');

-- Create Payments Table
CREATE TABLE Payments (
    payment_id SERIAL PRIMARY KEY,
    tenant_id INTEGER,
    amount NUMERIC(10, 2) NOT NULL,
    date DATE NOT NULL,
    status TEXT DEFAULT 'Pending',
    payment_method TEXT,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(tenant_id)
);

-- Insert into Payments
INSERT INTO Payments VALUES(DEFAULT,11,15000.0,'2024-09-03','Pending','Cash');
INSERT INTO Payments VALUES(DEFAULT,13,8500.0,'2024-09-01','Paid','Cash');
INSERT INTO Payments VALUES(DEFAULT,12,8500.0,'2024-09-01','Paid','Cash');

-- Create Complaints Table
CREATE TABLE Complaints (
    complaint_id SERIAL PRIMARY KEY,
    tenant_id INTEGER,
    description TEXT NOT NULL,
    date DATE NOT NULL,
    status TEXT DEFAULT 'Open',
    FOREIGN KEY (tenant_id) REFERENCES Tenants(tenant_id)
);

-- Insert into Complaints
INSERT INTO Complaints VALUES(DEFAULT,11,'test#2 working or not','2024-09-16','Open');
INSERT INTO Complaints VALUES(DEFAULT,11,replace(replace('Test#3 working or not\r\n','\r',chr(13)),'\n',chr(10)),'2024-09-16','Open');
INSERT INTO Complaints VALUES(DEFAULT,13,replace(replace('Test#1 complaine 1\r\n','\r',chr(13)),'\n',chr(10)),'2024-09-20','Open');
INSERT INTO Complaints VALUES(DEFAULT,13,'Test#2 complaint 2','2024-09-20','Open');

-- Create Feedback Table
CREATE TABLE Feedback (
    feedback_id SERIAL PRIMARY KEY,
    tenant_id INTEGER,
    feedback TEXT NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES Tenants(tenant_id)
);

-- Create Menu Table
CREATE TABLE Menu (
    menu_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    meal_type TEXT NOT NULL,
    items TEXT
);

-- Insert into Menu
INSERT INTO Menu VALUES(DEFAULT,'2024-09-15','Lunch','Sambar rice');

-- Create Users Table
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
);

-- Insert into Users
INSERT INTO Users VALUES(DEFAULT,'admin','scrypt:32768:8:1$6cRzBcqEkSJztqup$1a056f4d6d69bc2ed38d7ccf9a2a0c0a1ff2b6276223c6d5132d537afab219d537b323d7c3f0b14335d6588562ef2db5b877de3521f9dcaccfbf417529a7a8d2','Admin');
INSERT INTO Users VALUES(DEFAULT,'abc@gmail.com','scrypt:32768:8:1$QE1lOR1dNM8Ch4Qy$28cb9aa225d35b5a8f750351f220e3c1ec8cda67810739d22643ff97da30c51e0f3ec5dd32fccb50c1469a8703d89f497e4a2d14cefa0f033f9efda6c717e4a9','Tenant');

-- Create Rooms Table
CREATE TABLE Rooms (
    room_number INTEGER PRIMARY KEY,
    status TEXT NOT NULL
);

-- Insert into Rooms
INSERT INTO Rooms VALUES(101,'occupied');
INSERT INTO Rooms VALUES(102,'available');
INSERT INTO Rooms VALUES(103,'available');
INSERT INTO Rooms VALUES(104,'available');
INSERT INTO Rooms VALUES(105,'available');
INSERT INTO Rooms VALUES(106,'available');
INSERT INTO Rooms VALUES(107,'available');
INSERT INTO Rooms VALUES(108,'available');
INSERT INTO Rooms VALUES(109,'available');
INSERT INTO Rooms VALUES(201,'available');
INSERT INTO Rooms VALUES(202,'available');
INSERT INTO Rooms VALUES(203,'available');
INSERT INTO Rooms VALUES(204,'available');
INSERT INTO Rooms VALUES(205,'available');
INSERT INTO Rooms VALUES(206,'available');
INSERT INTO Rooms VALUES(207,'available');
INSERT INTO Rooms VALUES(208,'available');
INSERT INTO Rooms VALUES(209,'available');

COMMIT;
