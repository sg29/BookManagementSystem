-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS bookstore;

-- Connect to the database
\c bookstore;

-- Create the books table
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    genre VARCHAR(100),
    year_published INTEGER,
    summary TEXT
);

-- Create the reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    user_id INTEGER,
    review_text TEXT,
    rating INTEGER
);

-- Create the reviews summary table
CREATE TABLE reviews_summary (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL,
    review_summary TEXT NOT NULL,
    rating_summary TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
