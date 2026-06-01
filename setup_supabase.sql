-- Run this in your Supabase SQL Editor (https://supabase.com/dashboard → SQL Editor)
-- This creates all tables needed for the World Cup Predictor app.

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS predictions (
    username TEXT REFERENCES users(username),
    match_id TEXT,
    home_score INTEGER,
    away_score INTEGER,
    PRIMARY KEY (username, match_id)
);

CREATE TABLE IF NOT EXISTS knockout_predictions (
    username TEXT REFERENCES users(username),
    round TEXT,
    match_index INTEGER,
    field TEXT,
    value TEXT,
    PRIMARY KEY (username, round, match_index, field)
);

CREATE TABLE IF NOT EXISTS official_results (
    match_id TEXT PRIMARY KEY,
    home_score INTEGER,
    away_score INTEGER
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
