CREATE DATABASE IF NOT EXISTS biharyatrasetu;
USE biharyatrasetu;

CREATE TABLE destinations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    location VARCHAR(100),
    description TEXT,
    image VARCHAR(255)
);

CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    destination_id INT,
    booking_date DATE,
    guide_required BOOLEAN,
    transport_required BOOLEAN,
    stay_required BOOLEAN,
    FOREIGN KEY (destination_id) REFERENCES destinations(id)
);

CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    destination_id INT,
    review TEXT,
    date_posted DATE,
    FOREIGN KEY (destination_id) REFERENCES destinations(id)
);
