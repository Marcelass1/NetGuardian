from flask import Flask, render_template, jsonify, request, send_file, redirect, session, url_for
from network_engine import NetworkEngine
from report_generator import generate_weekly_report
import database
import threading
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'superdev_secret_key'

# Initialize Database
database.init_db()

engine = NetworkEngine()
ACCESS_LOGS = []

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
            
            # Log incident if status changed to DOWN
            # Only log if we had a previous status (not just 'Checking...')
            if HOST_STATE[hid]['status'] == "UP" and new_status == "DOWN":
                engine.log_incident(host['name'])
                
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
                
                # Update DB only if changed (optional optimization, but we just write for now to be safe)
                if svc.get('status') != status:
                    database.update_service_status(sid, status)

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
            log_access(user, False, request.remote_addr)
            error = 'Identifiants Invalides. Essayez admin/admin.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/api/status')
def api_status():
    # Merge DB config with Runtime State
    db_hosts = database.get_hosts()
    response = []
    
    # Calculate global warning count
    warnings = 0
    
    for h in db_hosts:
        hid = h['id']
        state = HOST_STATE.get(hid, {'status': 'Pending', 'history': [], 'last_check': '-'})
        
        # Get services and their status (directly from DB now)
        services = database.get_services(hid)
        service_data = []
        for svc in services:
            sid = svc['id']
            # Default to Checking if new column is somehow empty (shouldn't happen with default)
            status = svc['status'] if svc['status'] else "Checking..."
            if status == "DOWN": warnings += 1
            service_data.append({
                "id": sid, "name": svc['name'], "port": svc['port'], "status": status
            })
            
        response.append({
            "id": hid,
            "name": h['name'],
            "ip": h['ip'],
            "status": state['status'],
            "history": state['history'],
            "last_check": state['last_check'],
            "services": service_data
        })
        
    return jsonify({"hosts": response, "warnings": warnings})

@app.route('/api/host', methods=['POST'])
def add_host():
    data = request.json
    name = data.get('name')
    ip = data.get('ip')
    if name and ip:
        if database.add_host(name, ip):
            return jsonify({"message": "Host added"}), 201
        else:
            return jsonify({"message": "IP already exists"}), 400
    return jsonify({"message": "Invalid data"}), 400

@app.route('/api/host/<int:host_id>', methods=['DELETE'])
def delete_host(host_id):
    database.delete_host(host_id)
    return jsonify({"message": "Host deleted"}), 200

@app.route('/api/service', methods=['POST'])
def add_service():
    data = request.json
    host_id = data.get('host_id')
    port = data.get('port')
    name = data.get('name')
    if host_id and port and name:
        if database.add_service(host_id, int(port), name):
            return jsonify({"message": "Service added"}), 201
    return jsonify({"message": "Error adding service"}), 400

@app.route('/api/service/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    database.delete_service(service_id)
    return jsonify({"message": "Service deleted"}), 200

@app.route('/map')
def network_map():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('network_map.html')

@app.route('/api/health')
def api_health():
    return jsonify(engine.get_server_health())

@app.route('/api/scan/vuln', methods=['POST'])
def api_vuln():
    ip = request.json.get('ip')
    return jsonify(engine.scan_vulnerabilities(ip))

@app.route('/api/scan/arp')
def api_arp():
    return jsonify(engine.get_connected_devices())

@app.route('/api/wol', methods=['POST'])
def api_wol():
    mac = request.json.get('mac')
    return jsonify({"message": engine.wake_on_lan(mac)})

@app.route('/api/terminal', methods=['POST'])
def api_terminal():
    cmd = request.json.get('cmd')
    host = request.json.get('host')
    if cmd == 'traceroute':
        return jsonify({"output": engine.run_traceroute(host)})
    return jsonify({"output": "Unknown command"})

@app.route('/api/speedtest')
def api_speedtest():
    return jsonify(engine.measure_speed())

@app.route('/api/scan/ports', methods=['POST'])
def api_portscan():
    ip = request.json.get('ip')
    return jsonify(engine.scan_ports(ip))

@app.route('/download/report')
def download_report():
    stats = engine.get_statistics()
    filename = generate_weekly_report(stats)
    if filename:
        return send_file(filename, as_attachment=True)
    return "Error generating PDF."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
