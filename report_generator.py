from datetime import datetime
import os
import platform
import socket

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

class ProReport(FPDF):
    def header(self):
        # Logo Text
        self.set_font('Arial', 'B', 20)
        self.set_text_color(0, 204, 102) # Green
        self.cell(80, 10, 'NetGuardian', 0, 0, 'L')
        
        # Sub-header
        self.set_font('Arial', '', 10)
        self.set_text_color(100, 100, 100) # Grey
        self.cell(0, 10, 'Audit Réseau & Sécurité Professionnel', 0, 1, 'R')
        
        # Line
        self.set_fill_color(0, 0, 0)
        self.cell(0, 1, '', 0, 1, 'L', 1)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Rapport Confidentiel | Généré par NetGuardian Pro | Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f'  {title}', 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, body)
        self.ln()

def generate_weekly_report(stats):
    if FPDF is None: return None

    filename = f"Rapport_NetGuardian_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    pdf = ProReport()
    pdf.add_page()
    
    # --- EXECUTIVE SUMMARY ---
    pdf.chapter_title('1. RÉSUMÉ EXÉCUTIF')
    summary_text = (
        f"Ce rapport documente l'état de sécurité et de performance de l'infrastructure réseau. "
        f"L'audit a été initié le {datetime.now().strftime('%d/%m/%Y')} à {datetime.now().strftime('%H:%M:%S')}.\n\n"
        f"État Global du Système: {'STABLE' if stats.get('incidents', 0) == 0 else 'ATTENTION'}\n"
        f"Disponibilité Totale (Uptime): {stats.get('uptime', '0%')}\n"
        f"Incidents Détectés: {stats.get('incidents', 0)}"
    )
    pdf.chapter_body(summary_text)

    # --- SYSTEM INFORMATION ---
    pdf.chapter_title('2. INFORMATIONS SYSTÈME HÔTE')
    
    # Table Header
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(60, 8, 'Propriété', 1, 0, 'C', 1)
    pdf.cell(130, 8, 'Détails', 1, 1, 'C', 1)
    
    # Table Rows
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    sys_info = [
        ("Nom d'hôte", socket.gethostname()),
        ("Système d'exploitation", f"{platform.system()} {platform.release()}"),
        ("Architecture", platform.machine()),
        ("Version Python", platform.python_version()),
        ("Durée Session", stats.get('duration', '0h'))
    ]
    
    for item in sys_info:
        pdf.cell(60, 8, item[0], 1)
        pdf.cell(130, 8, item[1], 1, 1)
    
    pdf.ln(10)

    # --- INCIDENT LOGS ---
    pdf.chapter_title('3. JOURNAL DES INCIDENTS DE SÉCURITÉ')
    
    logs = stats.get('incident_log', [])
    if not logs:
        pdf.set_text_color(0, 128, 0) # Green
        pdf.cell(0, 10, "[OK] Aucun incident critique détecté durant cette session.", 0, 1)
    else:
        pdf.set_fill_color(255, 230, 230) # Red tint
        pdf.set_text_color(200, 0, 0)
        pdf.font_size = 10
        for incident in logs:
            pdf.cell(0, 8, f" [CRITIQUE] {incident['time']} - Cible {incident['target']} est INACCESSIBLE", 1, 1, 'L', 1)
            
    pdf.ln(10)
    
    # --- RECOMMENDATIONS ---
    pdf.chapter_title('4. RECOMMANDATIONS')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, 
        "- Maintenir des sauvegardes régulières de la configuration système.\n"
        "- S'assurer que tous les appareils connectés sont autorisés (Voir Scan ARP).\n"
        "- Vérifier périodiquement les ports ouverts pour prévenir les accès non autorisés.\n"
        "- Mettre à jour ce logiciel régulièrement."
    )
    
    # --- SIGNATURE ---
    pdf.ln(20)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(120, pdf.get_y(), 190, pdf.get_y())
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, "Signature Administrateur Autorisée", 0, 1, 'R')

    path = os.path.join(os.getcwd(), filename)
    pdf.output(path)
    return filename

def generate_audit_report(scan_data):
    if FPDF is None: return None
    
    filename = f"Audit_Securite_{scan_data.get('ip', 'target').replace('.', '-')}_{datetime.now().strftime('%H%M')}.pdf"
    pdf = ProReport()
    pdf.add_page()
    
    # --- HEADER ---
    pdf.chapter_title(f"AUDIT CIBLE: {scan_data.get('ip', 'N/A')}")
    
    score_color = (0, 204, 102) # Green
    if scan_data.get('score', 0) < 50: score_color = (255, 50, 50) # Red
    elif scan_data.get('score', 0) < 80: score_color = (255, 165, 0) # Orange
    
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(*score_color)
    pdf.cell(0, 10, f"NOTE GLOBALE: {scan_data.get('grade', 'N/A')} ({scan_data.get('score', 0)}/100)", 0, 1, 'C')
    pdf.ln(10)

    # --- VULNERABILITIES ---
    pdf.chapter_title('DÉTAILS DES VULNÉRABILITÉS')
    
    vulns = scan_data.get('vulnerabilities', [])
    if not vulns:
        pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 10, "Aucune vulnérabilité critique détectée.", 0, 1)
    else:
        # Tips Database
        TIPS = {
            21: "Le protocole FTP n'est pas chiffré. Utilisez SFTP ou FTPS.",
            22: "Assurez-vous que SSH utilise des clés et non des mots de passe. Changez le port par défaut.",
            23: "Telnet est obsolète et non sécurisé. Migrez impérativement vers SSH.",
            80: "Le trafic HTTP est en clair. Installez un certificat SSL/TLS (HTTPS).",
            445: "SMB est une cible privilégiée pour les ransomwares. Bloquez le port 445 depuis Internet.",
            3306: "La base de données ne devrait pas être exposée publiquement. Utilisez un VPN ou Tunnel SSH."
        }
        
        pdf.set_font('Arial', '', 10)
        for v in vulns:
            port = v.get('port', 0)
            issue = v.get('issue', 'Unknown')
            
            # Box
            pdf.set_fill_color(245, 245, 245)
            pdf.set_text_color(0, 0, 0)
            pdf.rect(pdf.get_x(), pdf.get_y(), 190, 25, 'F')
            
            # Content
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(15, 8, f"PORT {port}", 0, 0)
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 8, f" - {issue}", 0, 1)
            
            # Tip
            pdf.set_text_color(100, 100, 100)
            pdf.set_font('Arial', 'I', 9)
            tip = TIPS.get(port, "Vérifiez la configuration de ce service et limitez son accès.")
            pdf.multi_cell(0, 5, f"CONSEIL: {tip}")
            pdf.ln(5)

    pdf.ln(10)
    
    # --- FOOTER SIGNATURE ---
    pdf.set_text_color(0,0,0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, "Rapport généré automatiquement par NetGuardian Pro.", 0, 1, 'C')

    path = os.path.join(os.getcwd(), filename)
    pdf.output(path)
    return filename
