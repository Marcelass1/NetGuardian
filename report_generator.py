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
