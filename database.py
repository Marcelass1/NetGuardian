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
        conn.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL,
                port INTEGER NOT NULL,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'Checking...',
                FOREIGN KEY(host_id) REFERENCES hosts(id) ON DELETE CASCADE
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

def add_service(host_id, port, name):
    conn = get_db_connection()
    with conn:
        conn.execute("INSERT INTO services (host_id, port, name, status) VALUES (?, ?, ?, 'Checking...')", (host_id, port, name))
    conn.close()
    return True

def get_services(host_id):
    conn = get_db_connection()
    services = conn.execute("SELECT * FROM services WHERE host_id = ?", (host_id,)).fetchall()
    conn.close()
    return [dict(ix) for ix in services]

def update_service_status(service_id, status):
    conn = get_db_connection()
    with conn:
        conn.execute("UPDATE services SET status = ? WHERE id = ?", (status, service_id))
    conn.close()

def delete_service(service_id):
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM services WHERE id = ?", (service_id,))
    conn.close()
