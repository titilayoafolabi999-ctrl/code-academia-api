CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT,
    created TEXT
);

CREATE TABLE IF NOT EXISTS courses (
    name TEXT PRIMARY KEY,
    price INTEGER
);

CREATE TABLE IF NOT EXISTS weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT,
    week INTEGER,
    title TEXT,
    lesson TEXT
);

CREATE TABLE IF NOT EXISTS progress (
    email TEXT,
    course TEXT,
    week INTEGER,
    passed_quiz BOOLEAN
);

CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT,
    week INTEGER,
    question TEXT,
    options TEXT,  -- Comma-separated options
    answer TEXT
);

CREATE TABLE IF NOT EXISTS codes (
    code TEXT PRIMARY KEY,
    used BOOLEAN,
    created TEXT
);
