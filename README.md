# 🛡️ NetGuardian Pro - Network Administration Suite

**NetGuardian** is a comprehensive Network Supervision & Administration tool developed in Python (Flask). It provides a real-time web dashboard to monitor network health, scan for devices, audit security, and generate professional PDF reports.

![NetGuardian Dashboard](https://i.imgur.com/example_dashboard_image.png)

## 🚀 Features

### 📡 Supervision & Monitoring
*   **Real-time Status**: Monitors Critical Hosts (Router, DNS, Localhost) with live updates.
*   **Sparkline Graphs**: Visual history of up/down status.
*   **Server Health**: Live CPU & RAM usage tracking.

### 🛠️ Administration Tools
*   **ARP Scout**: Scans the local network to find connected devices (IP, MAC, Vendor).
*   **Speedtest**: Measures Internet Bandwidth (Download/Upload/Ping).
*   **Wake-on-LAN**: Remotely wake up devices using Magic Packets.
*   **Web Terminal**: Run traceroute and network diagnostics from the browser.

### 🔐 Security Audit
*   **Vulnerability Scanner**: Checks hosts for dangerous open ports (FTP, Telnet, SMB).
*   **Access Logs**: Tracks all successful and failed login attempts.
*   **Port Inspector**: Detailed port scanning for specific targets.

### 📄 Reporting
*   **Professional PDF Export**: Generates a detailed audit report with:
    *   Executive Summary
    *   System Information
    *   Incident Logs
    *   Recommendations

## 💻 Tech Stack
*   **Backend**: Python 3.12, Flask
*   **Frontend**: HTML5, CSS3 (Glassmorphism/HUD Themes), JavaScript
*   **Libraries**: `scapy` (Scanning), `psutil` (System Info), `fpdf` (PDFs), `speedtest-cli`

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/NetGuardian.git
    cd NetGuardian
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**:
    ```bash
    python app.py
    ```

4.  **Access the Dashboard**:
    Open `http://localhost:5000` in your browser.
    *   **Login**: `admin` / `admin`

## 📜 License
This project was developed as a PFE (End of Studies Project) for Network & Systems Administration.
