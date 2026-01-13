from flask import Flask, render_template, jsonify, request, send_file, redirect, session, url_for
from network_engine import NetworkEngine
from report_generator import generate_weekly_report
import threading
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'superdev_secret_key'

engine = NetworkEngine()
ACCESS_LOGS = []

def log_access(username, success, ip):
    status = "SUCCESS" if success else "FAILED"
    ACCESS_LOGS.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": username,
        "status": status,
        "ip": ip
    })
    if len(ACCESS_LOGS) > 50: ACCESS_LOGS.pop()

TARGETS = [
    {"name": "Router (Gateway)", "ip": "192.168.1.1", "status": "Checking...", "history": []},
    {"name": "Google DNS", "ip": "8.8.8.8", "status": "Checking...", "history": []},
    {"name": "Localhost", "ip": "127.0.0.1", "status": "Checking...", "history": []}
]

def monitor_loop():
    while True:
        for target in TARGETS:
            is_up = engine.ping_host(target['ip'])
            new_status = "UP" if is_up else "DOWN"
            
            # Log incident if status changed to DOWN
            if target['status'] == "UP" and new_status == "DOWN":
                engine.log_incident(target['name'])
                
            target['status'] = new_status
            target['last_check'] = time.strftime("%H:%M:%S")
            
            # Add sparkline data
            # 1 = UP, 0 = DOWN
            target['history'].append(1 if is_up else 0)
            if len(target['history']) > 20: target['history'].pop(0)
            
        time.sleep(2) # Faster checking for smoother UI

t = threading.Thread(target=monitor_loop, daemon=True)
t.start()

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', targets=TARGETS, logs=ACCESS_LOGS)

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
    return jsonify(TARGETS)

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
