import sqlite3
import os

DB_NAME = "netguardian.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ip TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Seed initial data if empty
        cur = conn.execute("SELECT count(*) FROM hosts")
        if cur.fetchone()[0] == 0:
            conn.execute("INSERT INTO hosts (name, ip) VALUES (?, ?)", ('Router (Gateway)', '192.168.1.1'))
            conn.execute("INSERT INTO hosts (name, ip) VALUES (?, ?)", ('Google DNS', '8.8.8.8'))
            conn.execute("INSERT INTO hosts (name, ip) VALUES (?, ?)", ('Localhost', '127.0.0.1'))
            print("Database initialized with default hosts.")
            
    conn.close()

def add_host(name, ip):
    try:
        conn = get_db_connection()
        with conn:
            conn.execute("INSERT INTO hosts (name, ip) VALUES (?, ?)", (name, ip))
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False # Duplicate IP

def get_hosts():
    conn = get_db_connection()
    hosts = conn.execute("SELECT * FROM hosts").fetchall()
    conn.close()
    return [dict(ix) for ix in hosts]

def delete_host(host_id):
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM hosts WHERE id = ?", (host_id,))
    conn.close()
