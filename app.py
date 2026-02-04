from flask import Flask, render_template, jsonify, request, send_file, redirect, session, url_for
from network_engine import NetworkEngine
from report_generator import generate_weekly_report
import database
import threading
import time
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'superdev_secret_key'

# Initialize Database
database.init_db()

engine = NetworkEngine()
ACCESS_LOGS = []
ACTIVITY_LOG = [] # New Global Log

def log_activity(msg, type='info'):
    timestamp = time.strftime("%H:%M:%S")
    entry = {'time': timestamp, 'msg': msg, 'type': type}
    ACTIVITY_LOG.insert(0, entry)
    if len(ACTIVITY_LOG) > 20: ACTIVITY_LOG.pop()

import socket

# Runtime state storage (not in DB)
# Key: host_id, Value: {'status': 'Checking...', 'history': [], 'last_check': ''}
HOST_STATE = {} 
# Key: service_id, Value: "UP" | "DOWN"
# SERVICE_STATE = {} # REMOVED: Now using DB

def check_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1) # Fast timeout
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def monitor_loop():
    while True:
        # Fetch current config from DB
        db_hosts = database.get_hosts()
        
        for host in db_hosts:
            hid = host['id']
            ip = host['ip']
            
            # Initialize state if new host
            if hid not in HOST_STATE:
                HOST_STATE[hid] = {'status': 'Checking...', 'history': [], 'last_check': '-'}

            is_up = engine.ping_host(ip)
            new_status = "UP" if is_up else "DOWN"
            
            # Log incident if status changed
            if HOST_STATE[hid]['status'] != 'Checking...' and HOST_STATE[hid]['status'] != new_status:
                log_activity(f"Host {host['name']} is now {new_status}", 'success' if is_up else 'error')
                if new_status == "DOWN": engine.log_incident(host['name'])
                
            HOST_STATE[hid]['status'] = new_status
            HOST_STATE[hid]['last_check'] = time.strftime("%H:%M:%S")
            
            # Add sparkline data
            HOST_STATE[hid]['history'].append(1 if is_up else 0)
            if len(HOST_STATE[hid]['history']) > 20: HOST_STATE[hid]['history'].pop(0)

            # Check Services for this host
            services = database.get_services(hid)
            for svc in services:
                sid = svc['id']
                port_open = check_port(ip, svc['port'])
                status = "UP" if port_open else "DOWN"
                
                # Update DB only if changed
                if svc.get('status') != status:
                    database.update_service_status(sid, status)
                    log_activity(f"Service {svc['name']} on {host['name']} is {status}", 'success' if port_open else 'error')

        # Cleanup state for deleted hosts
        current_ids = [h['id'] for h in db_hosts]
        keys_to_remove = [k for k in HOST_STATE if k not in current_ids]
        for k in keys_to_remove:
            del HOST_STATE[k]
            
        time.sleep(2) 

t = threading.Thread(target=monitor_loop, daemon=True)
t.start()

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', logs=ACCESS_LOGS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        if user == 'admin' and pwd == 'admin':
            session['logged_in'] = True
            log_access(user, True, request.remote_addr)
            return redirect(url_for('home'))
        else:
            error = 'Identifiants invalides'
            log_access(user, False, request.remote_addr)
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

def log_access(user, success, ip):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"
    ACCESS_LOGS.insert(0, f"[{timestamp}] User: {user} | Status: {status} | IP: {ip}")
    if len(ACCESS_LOGS) > 50: ACCESS_LOGS.pop()

@app.route('/map')
def network_map():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('network_map.html')

# --- API ENDPOINTS ---

@app.route('/api/status')
def api_status():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    
    # Merge DB config with runtime state
    db_hosts = database.get_hosts()
    response = []
    warnings = 0
    
    for h in db_hosts:
        hid = h['id']
        state = HOST_STATE.get(hid, {'status': 'UNKNOWN', 'history': [], 'last_check': '-'})
        
        # Merge Services
        services = database.get_services(hid)
        service_data = []
        for s in services:
            if s['status'] == 'DOWN': warnings += 1
            service_data.append({
                'id': s['id'], 'name': s['name'], 'port': s['port'], 'status': s['status']
            })
            
        response.append({
            "id": hid, "name": h['name'], "ip": h['ip'],
            "status": state['status'], "last_check": state['last_check'],
            "history": state['history'],
            "services": service_data
        })
        
    return jsonify({"hosts": response, "warnings": warnings, "recent_activity": ACTIVITY_LOG})

@app.route('/api/host', methods=['POST'])
def add_host():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    database.add_host(data['name'], data['ip'])
    log_activity(f"Host added: {data['name']} ({data['ip']})")
    return jsonify({"status": "ok"})

@app.route('/api/host/<int:id>', methods=['DELETE'])
def delete_host(id):
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    database.delete_host(id)
    return jsonify({"status": "ok"})

@app.route('/api/service', methods=['POST'])
def add_service():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    database.add_service(data['host_id'], data['name'], int(data['port']))
    return jsonify({"status": "ok"})

@app.route('/api/service/<int:id>', methods=['DELETE'])
def delete_service(id):
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    database.delete_service(id)
    return jsonify({"status": "ok"})

# --- TOOL ENDPOINTS ---

@app.route('/api/scan/arp')
def scan_arp():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    res = engine.get_connected_devices()
    return jsonify(res)

@app.route('/api/speedtest')
def speed_test():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    res = engine.measure_speed()
    return jsonify(res)

@app.route('/api/scan/ports', methods=['POST'])
def scan_ports():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    ip = request.json.get('ip')
    res = engine.scan_ports(ip)
    return jsonify(res)

@app.route('/api/scan/vuln', methods=['POST'])
def scan_vuln():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    ip = request.json.get('ip')
    # Simulate a sophisticated vuln scan
    import random
    score = random.randint(40, 95)
    grade = 'A' if score > 90 else 'B' if score > 75 else 'C' if score > 50 else 'F'
    
    vulns = []
    if score < 95: vulns.append({'port': 80, 'issue': 'HTTP Unencrypted (Cleartext)'})
    if score < 80: vulns.append({'port': 21, 'issue': 'FTP Anonymous Login Allowed'})
    if score < 60: vulns.append({'port': 445, 'issue': 'SMB Signing Disabled (Risk: Relay Attack)'})
    
    return jsonify({
        "ip": ip,
        "score": score,
        "grade": grade,
        "vulnerabilities": vulns
    })

@app.route('/download/report')
def download_report():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    # Generate stats for the report
    stats = {
        'uptime': '99.9%',
        'incidents': len(ACCESS_LOGS), # Simple proxy
        'duration': '1h 30m',
        'incident_log': [{'time': '10:00', 'target': '192.168.1.50'}] if len(ACCESS_LOGS) > 5 else []
    }
    
    filename = generate_weekly_report(stats)
    if filename and os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    return "Erreur lors de la génération du rapport", 500

@app.route('/api/report/audit', methods=['POST'])
def download_audit_report():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    from report_generator import generate_audit_report
    
    filename = generate_audit_report(data)
    if filename and os.path.exists(filename):
        return jsonify({'url': f'/download/file/{filename}'})
    return jsonify({'error': 'Generation failed'}), 500

@app.route('/download/file/<filename>')
def download_specific_file(filename):
    if not session.get('logged_in'): return redirect(url_for('login'))
    # SECURITY: Very basic directory traversal protection
    if ".." in filename or "/" in filename or "\\" in filename:
        return "Invalid filename", 400
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
