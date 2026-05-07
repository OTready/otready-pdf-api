from flask import Flask, request, send_file, jsonify
import io
import json
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, HRFlowable, KeepTogether)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
import math

app = Flask(__name__)

# ── PALETTE ──────────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#1F3A5F")
BLUE       = colors.HexColor("#2E75B6")
LIGHT_BLUE = colors.HexColor("#D6E4F0")
MID_BLUE   = colors.HexColor("#BDD7EE")
RED        = colors.HexColor("#C00000")
RED_LIGHT  = colors.HexColor("#FDECEA")
AMBER      = colors.HexColor("#ED7D31")
AMBER_LIGHT= colors.HexColor("#FEF3E2")
GREEN      = colors.HexColor("#375623")
GREEN_LIGHT= colors.HexColor("#E2EFDA")
GRAY       = colors.HexColor("#F5F5F5")
GRAY_MID   = colors.HexColor("#D9D9D9")
WHITE      = colors.white
TEXT_DARK  = colors.HexColor("#1A1A1A")
TEXT_MID   = colors.HexColor("#444444")
TEXT_LIGHT = colors.HexColor("#777777")

H = A4[1]

def make_styles():
    return {
        'cover_title': ParagraphStyle('cover_title', fontName='Helvetica-Bold',
            fontSize=28, textColor=NAVY, leading=34, spaceAfter=6),
        'h1': ParagraphStyle('h1', fontName='Helvetica-Bold',
            fontSize=13, textColor=WHITE, leading=17,
            backColor=NAVY, spaceBefore=14, spaceAfter=8,
            borderPadding=(6,12,6,12)),
        'h2': ParagraphStyle('h2', fontName='Helvetica-Bold',
            fontSize=11, textColor=WHITE, leading=15,
            backColor=BLUE, spaceBefore=10, spaceAfter=6,
            borderPadding=(5,8,5,8)),
        'h3': ParagraphStyle('h3', fontName='Helvetica-Bold',
            fontSize=10.5, textColor=NAVY, leading=14,
            spaceBefore=8, spaceAfter=4),
        'body': ParagraphStyle('body', fontName='Helvetica',
            fontSize=9.5, textColor=TEXT_DARK, leading=14,
            spaceBefore=2, spaceAfter=4),
        'body_small': ParagraphStyle('body_small', fontName='Helvetica',
            fontSize=8.5, textColor=TEXT_MID, leading=12,
            spaceBefore=2, spaceAfter=2),
        'bullet': ParagraphStyle('bullet', fontName='Helvetica',
            fontSize=9.5, textColor=TEXT_DARK, leading=13,
            leftIndent=14, firstLineIndent=-10,
            spaceBefore=2, spaceAfter=2),
        'bullet_bold': ParagraphStyle('bullet_bold', fontName='Helvetica-Bold',
            fontSize=9.5, textColor=NAVY, leading=13,
            leftIndent=14, firstLineIndent=-10,
            spaceBefore=6, spaceAfter=1),
        'caption': ParagraphStyle('caption', fontName='Helvetica-Oblique',
            fontSize=8, textColor=TEXT_LIGHT, leading=10, spaceAfter=6),
        'disclaimer': ParagraphStyle('disclaimer', fontName='Helvetica-Oblique',
            fontSize=8, textColor=TEXT_LIGHT, leading=11,
            spaceBefore=4, spaceAfter=4),
    }

def status_color(score):
    if score <= 1.2: return RED, RED_LIGHT, "FRAGILE"
    if score <= 2.2: return AMBER, AMBER_LIGHT, "INTERMEDIO"
    return GREEN, GREEN_LIGHT, "STRUTTURATO"

def on_page(canvas, doc):
    canvas.saveState()
    pw = A4[0]
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 1.4*cm, pw, 1.4*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.5*cm, H - 0.85*cm, "OTReady")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(pw - 1.5*cm, H - 0.85*cm, "OT Cyber Risk & Maturity Assessment Report")
    canvas.setFillColor(GRAY)
    canvas.rect(0, 0, pw, 1*cm, fill=1, stroke=0)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(1.5*cm, 0.35*cm, "Prodotto da: Riccardo Talarico  |  otready.tech")
    canvas.drawRightString(pw - 1.5*cm, 0.35*cm, f"Pagina {doc.page}")
    canvas.restoreState()

def on_cover(canvas, doc):
    canvas.saveState()
    pw = A4[0]
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 3*cm, pw, 3*cm, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, H - 3.3*cm, pw, 0.3*cm, fill=1, stroke=0)
    canvas.setFillColor(GRAY)
    canvas.rect(0, 0, pw, 1.2*cm, fill=1, stroke=0)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(1.5*cm, 0.45*cm, "Prodotto da: Riccardo Talarico  |  otready.tech")
    canvas.drawRightString(pw - 1.5*cm, 0.45*cm, "RISERVATO - USO INTERNO / CONSULENZIALE")
    canvas.restoreState()

def score_bar_chart(scores):
    labels = ["S1 Contesto OT", "S2 Architettura IT/OT",
              "S3 Accessi e Fornitori", "S4 Continuita Operativa",
              "S5 Change Management", "S6 Governance e Normativa"]
    d = Drawing(430, 200)
    bar_h, bar_gap, label_w, bar_max, y_start = 20, 8, 145, 220, 160
    for i, (label, val) in enumerate(zip(labels, scores)):
        y = y_start - i * (bar_h + bar_gap)
        col, bg, txt = status_color(val)
        d.add(String(label_w - 4, y + 5, label, fontName='Helvetica', fontSize=8,
                     fillColor=TEXT_DARK, textAnchor='end'))
        d.add(Rect(label_w, y, bar_max, bar_h, fillColor=GRAY, strokeColor=None, strokeWidth=0))
        bar_w = int((val / 3.0) * bar_max)
        if bar_w > 0:
            d.add(Rect(label_w, y, bar_w, bar_h, fillColor=col, strokeColor=None, strokeWidth=0))
        d.add(String(label_w + bar_max + 6, y + 5, f"{val:.2f}",
                     fontName='Helvetica-Bold', fontSize=8.5, fillColor=TEXT_DARK))
        d.add(String(label_w + bar_max + 38, y + 5, txt,
                     fontName='Helvetica-Bold', fontSize=7.5, fillColor=col))
    for v in [0, 1, 1.5, 2, 3]:
        x = label_w + int((v / 3.0) * bar_max)
        d.add(String(x, y_start - 6*(bar_h+bar_gap) - 14, str(v),
                     fontName='Helvetica', fontSize=7, fillColor=TEXT_LIGHT, textAnchor='middle'))
        d.add(Line(x, y_start - 6*(bar_h+bar_gap), x, y_start + bar_h,
                   strokeColor=GRAY_MID, strokeWidth=0.5))
    return d

def radar_chart(scores):
    labels = ["S1 Contesto", "S2 Architettura", "S3 Accessi",
              "S4 Continuita", "S5 Change", "S6 Governance"]
    n, cx, cy, r_max = 6, 130, 130, 90
    d = Drawing(260, 260)
    for level in [1, 2, 3]:
        r = int((level / 3.0) * r_max)
        for i in range(n):
            a1 = math.pi/2 - i * 2*math.pi/n
            a2 = math.pi/2 - (i+1) * 2*math.pi/n
            d.add(Line(cx + r*math.cos(a1), cy + r*math.sin(a1),
                       cx + r*math.cos(a2), cy + r*math.sin(a2),
                       strokeColor=GRAY_MID, strokeWidth=0.5))
    for i in range(n):
        angle = math.pi/2 - i * 2*math.pi/n
        d.add(Line(cx, cy, cx + r_max*math.cos(angle), cy + r_max*math.sin(angle),
                   strokeColor=GRAY_MID, strokeWidth=0.5))
    pts = []
    for i, val in enumerate(scores):
        angle = math.pi/2 - i * 2*math.pi/n
        r = (val / 3.0) * r_max
        pts.extend([cx + r*math.cos(angle), cy + r*math.sin(angle)])
    d.add(Polygon(pts, fillColor=colors.HexColor("#2E75B6"),
                  strokeColor=BLUE, strokeWidth=1.5, fillOpacity=0.3))
    for i, val in enumerate(scores):
        angle = math.pi/2 - i * 2*math.pi/n
        r = (val / 3.0) * r_max
        col, _, _ = status_color(val)
        d.add(Rect(cx + r*math.cos(angle) - 4, cy + r*math.sin(angle) - 4,
                   8, 8, fillColor=col, strokeColor=WHITE, strokeWidth=1))
    for i, label in enumerate(labels):
        angle = math.pi/2 - i * 2*math.pi/n
        lx = cx + (r_max + 18) * math.cos(angle)
        ly = cy + (r_max + 18) * math.sin(angle)
        d.add(String(lx, ly, label, fontName='Helvetica-Bold', fontSize=7,
                     fillColor=NAVY, textAnchor='middle'))
    return d

def h1(t, S): return Paragraph(t, S['h1'])
def h2(t, S): return Paragraph(t, S['h2'])
def h3(t, S): return Paragraph(t, S['h3'])
def body(t, S): return Paragraph(t, S['body'])
def sp(h=6): return Spacer(1, h)
def hr(): return HRFlowable(width="100%", thickness=0.5, color=LIGHT_BLUE, spaceAfter=6, spaceBefore=4)

def bullet(text, S, bold=False):
    st = S['bullet_bold'] if bold else S['bullet']
    return Paragraph(f"• {text}", st)

def callout(text, S):
    tbl = Table([[Paragraph(text, S['body'])]], colWidths=[430])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BLUE),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    return tbl

def norm_table(rows, S):
    bs = ParagraphStyle('bs2', fontName='Helvetica', fontSize=8, textColor=TEXT_DARK, leading=11)
    converted = []
    for row in rows:
        new_row = []
        for cell in row:
            if isinstance(cell, str):
                new_row.append(Paragraph(cell, bs))
            else:
                new_row.append(cell)
        converted.append(new_row)
    t = Table(converted, colWidths=[7*cm, 2.2*cm, 9.8*cm])
    style = [
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.3, GRAY_MID),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY]),
    ]
    stato_map = {"FRAGILE": (RED, RED_LIGHT), "PARZIALE": (AMBER, AMBER_LIGHT),
                 "INTERMEDIO": (AMBER, AMBER_LIGHT), "STRUTTURATO": (GREEN, GREEN_LIGHT),
                 "LIMITATO": (RED, RED_LIGHT), "CONFORME": (GREEN, GREEN_LIGHT)}
    for i in range(1, len(rows)):
        cell = rows[i][1]
        stato = cell if isinstance(cell, str) else ""
        for key, (col, bg) in stato_map.items():
            if key in stato.upper():
                style.extend([
                    ('BACKGROUND', (1,i), (1,i), bg),
                    ('TEXTCOLOR', (1,i), (1,i), col),
                    ('FONTNAME', (1,i), (1,i), 'Helvetica-Bold'),
                ])
                break
    t.setStyle(TableStyle(style))
    return t
def clean_html_for_reportlab(text):
    """Clean HTML tags that ReportLab cannot handle."""
    # Fix self-closing br tags
    text = re.sub(r'<br\s*/?>', ' ', text)
    # Remove para tags
    text = re.sub(r'</?para>', '', text)
    # Remove p tags but keep content
    text = re.sub(r'</?p>', ' ', text)
    # Remove strong/b tags but keep content  
    text = re.sub(r'<strong>(.*?)</strong>', r'\1', text)
    text = re.sub(r'<b>(.*?)</b>', r'\1', text)
    # Remove other HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Clean multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_report_text(report_text):
    """
    Parse the text report from Claude and extract structured data.
    Returns a dict with all the fields needed to build the PDF.
    """
    data = {
        'azienda': 'Non specificata',
        'settore': 'Non specificato',
        'dimensione': 'Non specificata',
        'nis2': 'Non specificato',
        'fornitori': 'Non specificato',
        'compilato_da': 'Non specificato',
        'email': '',
        'data': 'Non specificata',
        'score_global': 0.0,
        'icn': 0.0,
        'cap_rule': False,
        'livello': 'Non determinato',
        'scores': {'S1': 0.0, 'S2': 0.0, 'S3': 0.0, 'S4': 0.0, 'S5': 0.0, 'S6': 0.0},
        'messaggi': [],
        'full_text': report_text,
    }

    # Extract azienda
    m = re.search(r'Azienda[:\s]+([^\n|]+)', report_text)
    if m: data['azienda'] = m.group(1).strip().split('|')[0].strip()

    # Extract settore
    m = re.search(r'Settore[:\s]+([^\n|]+)', report_text)
    if m: data['settore'] = m.group(1).strip().split('|')[0].strip()

    # Extract dimensione
    m = re.search(r'Dimensione[:\s]+([^\n|]+)', report_text)
    if m: data['dimensione'] = m.group(1).strip().split('|')[0].strip()

    # Extract NIS2
    m = re.search(r'(?:Esposizione NIS2|NIS2)[:\s]+([^\n|]+)', report_text)
    if m: data['nis2'] = m.group(1).strip().split('|')[0].strip()

    # Extract fornitori
    m = re.search(r'Fornitori[^\n:]*[:\s]+([^\n|]+)', report_text)
    if m: data['fornitori'] = m.group(1).strip().split('|')[0].strip()

    # Extract compilato da
    m = re.search(r'Compilato da[:\s]+([^\n|–-]+)', report_text)
    if m: data['compilato_da'] = m.group(1).strip()

    # Extract email
    m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', report_text)
    if m: data['email'] = m.group(0)

    # Extract data
    m = re.search(r'Data[^:]*[:\s]+(\d{1,2}[^\n|]{3,20}\d{4})', report_text)
    if m: data['data'] = m.group(1).strip()

    # Extract score globale
    m = re.search(r'Score[^:]*[:\s]*([\d]+\.[\d]+)', report_text)
    if m: data['score_global'] = float(m.group(1))

    # Extract ICN
    m = re.search(r'ICN[:\s]*([\d]+\.[\d]+)', report_text)
    if m: data['icn'] = float(m.group(1))

    # Extract livello
    m = re.search(r'Livello\s+(\d+\s*[–-]\s*\w+)', report_text)
    if m: data['livello'] = m.group(1).strip()

    # Check cap rule
    if 'CAP RULE' in report_text.upper() and 'NON ATTIVA' not in report_text.upper():
        data['cap_rule'] = True

    # Extract section scores
    patterns = {
        'S1': r'S1[^:]*[:\s]*([\d]+\.[\d]+)',
        'S2': r'S2[^:]*[:\s]*([\d]+\.[\d]+)',
        'S3': r'S3[^:]*[:\s]*([\d]+\.[\d]+)',
        'S4': r'S4[^:]*[:\s]*([\d]+\.[\d]+)',
        'S5': r'S5[^:]*[:\s]*([\d]+\.[\d]+)',
        'S6': r'S6[^:]*[:\s]*([\d]+\.[\d]+)',
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, report_text)
        if m:
            data['scores'][key] = float(m.group(1))

    return data


def build_pdf_from_data(data, report_text):
    S = make_styles()
    scores_list = [data['scores'][f'S{i}'] for i in range(1, 7)]

    sections_meta = [
        ("S1 - Contesto OT e Criticita",   data['scores']['S1'], "10%"),
        ("S2 - Architettura IT/OT",         data['scores']['S2'], "20%"),
        ("S3 - Accessi e Fornitori",         data['scores']['S3'], "25%"),
        ("S4 - Continuita Operativa",        data['scores']['S4'], "20%"),
        ("S5 - Change Management",           data['scores']['S5'], "15%"),
        ("S6 - Governance e Formazione",     data['scores']['S6'], "10%"),
    ]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2.2*cm, bottomMargin=1.8*cm)

    story = []

    # ── COVER ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3.5*cm))
    story.append(Paragraph("OT Cyber Risk &amp; Maturity", S['cover_title']))
    story.append(Paragraph("Assessment Report", ParagraphStyle('ct2',
        fontName='Helvetica-Bold', fontSize=22, textColor=BLUE, leading=28, spaceAfter=4)))
    story.append(Paragraph("Valutazione di maturita e governance del rischio cyber OT",
        ParagraphStyle('cs', fontName='Helvetica-Oblique', fontSize=11,
                       textColor=TEXT_MID, leading=14, spaceAfter=20)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE, spaceAfter=16))

    meta = [["Azienda", data['azienda']], ["Settore", data['settore']],
            ["Dimensione", data['dimensione']], ["Esposizione NIS2", data['nis2']],
            ["Compilato da", data['compilato_da']], ["Data assessment", data['data']]]
    mt = Table(meta, colWidths=[4.5*cm, 11*cm])
    mt.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9.5),
        ('TEXTCOLOR', (0,0), (0,-1), NAVY),
        ('BACKGROUND', (0,0), (0,-1), LIGHT_BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10), ('GRID', (0,0), (-1,-1), 0.3, GRAY_MID),
    ]))
    story.append(mt)
    story.append(sp(16))
    story.append(Paragraph("<i>RISERVATO - USO INTERNO / CONSULENZIALE</i>",
        ParagraphStyle('conf', fontName='Helvetica-Oblique', fontSize=8, textColor=RED)))
    story.append(PageBreak())

    # ── 1. EXECUTIVE SUMMARY ──────────────────────────────────────────────────
    story.append(h1("1. Executive Summary", S))
    story.append(sp(4))

    g_col, g_bg, g_txt = status_color(data['score_global'])
    i_col, i_bg, i_txt = status_color(data['icn'])

    kpi = [[
        Paragraph(f"<b>Livello di Maturita OT</b><br/><br/>"
                  f"<font color='#{g_col.hexval()[2:]}' size=13><b>Livello {data['livello']}</b></font><br/>"
                  f"<font size=10><b>Score: {data['score_global']:.2f} / 3  -  {g_txt}</b></font>", S['body']),
        Paragraph(f"<b>Indice di Coerenza Normativa (ICN)</b><br/><br/>"
                  f"<font color='#{i_col.hexval()[2:]}' size=13><b>ICN: {data['icn']:.2f}</b></font><br/>"
                  f"<font size=10><b>{i_txt}</b></font>", S['body'])
    ]]
    kt = Table(kpi, colWidths=[9.5*cm, 9.5*cm])
    kt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), g_bg), ('BACKGROUND', (1,0), (1,0), i_bg),
        ('TOPPADDING', (0,0), (-1,-1), 12), ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 14), ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('BOX', (0,0), (0,0), 1, g_col), ('BOX', (1,0), (1,0), 1, i_col),
    ]))
    story.append(kt)
    story.append(sp(8))

    if data['cap_rule']:
        story.append(callout(
            "CAP RULE ATTIVA: Le sezioni Accessi (S3) e/o Continuita Operativa (S4) "
            "presentano criticita strutturali che limitano il livello complessivo raggiungibile. "
            "Anche migliorando altre aree, senza presidio su accessi e continuita il rischio operativo resta elevato.",
            S))
        story.append(sp(8))

    # Extract executive summary section from full text
    exec_match = re.search(r'Executive Summary.*?(?=\n#+\s*\d|$)', report_text, re.DOTALL | re.IGNORECASE)
    if exec_match:
        exec_text = exec_match.group(0)
        # Extract bullet points / messaggi chiave
        messaggi = re.findall(r'(?:^|\n)[*•-]\s*\*?\*?([^*\n]+)\*?\*?', exec_text)
        if messaggi:
            story.append(h3("Messaggi chiave per il management", S))
            for msg in messaggi[:6]:
                if len(msg.strip()) > 20:
                    story.append(bullet(msg.strip(), S, bold=True))
                    story.append(sp(2))

    story.append(PageBreak())

    # ── 2. PROFILO ────────────────────────────────────────────────────────────
    story.append(h1("2. Profilo della valutazione", S))
    story.append(sp(4))
    prof = [
        ["Azienda", data['azienda'], "Settore", data['settore']],
        ["Dimensione", data['dimensione'], "Fornitori accesso remoto OT", data['fornitori']],
        ["Esposizione NIS2", data['nis2'], "Compilato da", data['compilato_da']],
        ["Data assessment", data['data'], "Strumento", "OTReady v3.0"],
    ]
    pt = Table(prof, colWidths=[4.2*cm, 6.3*cm, 4.5*cm, 4*cm])
    pt.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('TEXTCOLOR', (0,0), (0,-1), NAVY), ('TEXTCOLOR', (2,0), (2,-1), NAVY),
        ('BACKGROUND', (0,0), (0,-1), LIGHT_BLUE), ('BACKGROUND', (2,0), (2,-1), LIGHT_BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('GRID', (0,0), (-1,-1), 0.3, GRAY_MID),
    ]))
    story.append(pt)
    story.append(sp(8))
    story.append(body("Questa valutazione e' basata su un questionario strutturato di 31 domande "
                      "(scala 0-3) organizzate in 6 domini operativi. Non e' un audit tecnico, "
                      "non certifica conformita normativa, non sostituisce penetration test o "
                      "valutazioni SCADA. L'obiettivo e' fornire al management una fotografia "
                      "pratica dello stato attuale e una roadmap concreta di miglioramento.", S))
    story.append(PageBreak())

    # ── 3. RISULTATI SINTETICI ────────────────────────────────────────────────
    story.append(h1("3. Risultati per sezione", S))
    story.append(sp(6))

    hdr = [Paragraph(f"<font color='white'><b>{t}</b></font>", S['body_small'])
           for t in ["Sezione", "Score", "Stato", "Peso"]]

    # Extract section summaries from report text
    section_summaries = {}
    for i, label in enumerate(['S1', 'S2', 'S3', 'S4', 'S5', 'S6']):
        pattern = rf'{label}[^:]*:\s*([\d.]+)[^\n]*\n([^\n]+)'
        m = re.search(pattern, report_text)
        if m:
            section_summaries[label] = m.group(2).strip()[:100]
        else:
            section_summaries[label] = ""

    rows = [hdr]
    for label, score, weight in sections_meta:
        key = label[:2]
        col, bg, txt = status_color(score)
        summary = section_summaries.get(key, "")
        row_data = [
            Paragraph(label, S['body_small']),
            Paragraph(f"<b>{score:.2f}</b>", ParagraphStyle('sv',
                fontName='Helvetica-Bold', fontSize=9, textColor=col, leading=11)),
            Paragraph(f"<b>{txt}</b>", ParagraphStyle('st',
                fontName='Helvetica-Bold', fontSize=8, textColor=col, leading=10)),
            Paragraph(weight, S['body_small']),
        ]
        rows.append(row_data)

    g_col2, g_bg2, g_txt2 = status_color(data['score_global'])
    rows.append([
        Paragraph("<font color='white'><b>SCORE GLOBALE PONDERATO</b></font>",
            ParagraphStyle('sg', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, leading=11)),
        Paragraph(f"<b>{data['score_global']:.2f}</b>",
            ParagraphStyle('sgv', fontName='Helvetica-Bold', fontSize=11, textColor=WHITE, leading=13)),
        Paragraph(f"<b>{g_txt2}</b>",
            ParagraphStyle('sgl', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, leading=10)),
        Paragraph(f"ICN: {data['icn']:.2f}",
            ParagraphStyle('icn', fontName='Helvetica', fontSize=8, textColor=WHITE, leading=10)),
    ])

    st_style = [
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('BACKGROUND', (0,-1), (-1,-1), NAVY),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('GRID', (0,0), (-1,-1), 0.3, GRAY_MID),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, GRAY]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]
    for i, (_, score, _) in enumerate(sections_meta):
        col, bg, _ = status_color(score)
        st_style.append(('BACKGROUND', (2,i+1), (2,i+1), bg))
    sec_tbl = Table(rows, colWidths=[6.5*cm, 1.5*cm, 2.5*cm, 8.5*cm])
    sec_tbl.setStyle(TableStyle(st_style))
    story.append(sec_tbl)
    story.append(sp(16))

    # Charts
    story.append(h3("3.1 Score per sezione", S))
    story.append(sp(4))
    story.append(score_bar_chart(scores_list))
    story.append(Paragraph(
        "Fig. 1 - Score per sezione (0-3). Rosso=Fragile, Arancio=Intermedio, Verde=Strutturato.",
        S['caption']))

    radar_block = [
        sp(12), h3("3.2 Profilo di maturita complessivo - Radar chart", S), sp(4),
        Table([[radar_chart(scores_list)]], colWidths=[19*cm],
              style=[('ALIGN',(0,0),(-1,-1),'CENTER')]),
        Paragraph("Fig. 2 - Radar chart del profilo di maturita OT per sezione.", S['caption'])
    ]
    story.append(KeepTogether(radar_block))
    story.append(PageBreak())

    # ── 4. CONTENUTO COMPLETO DEL REPORT ──────────────────────────────────────
    # Insert the full report text as formatted content
    story.append(h1("4. Analisi dettagliata e Raccomandazioni", S))
    story.append(sp(6))

    # Parse and render the full report text
    lines = report_text.split('\n')
    for line in lines:
        line = clean_html_for_reportlab(line.strip())
        if not line:
            story.append(sp(4))
            continue

        # Skip lines that are just score summaries (already shown above)
        if re.match(r'^Score Globale|^ICN:|^Cap rule|^CALCOLO', line, re.IGNORECASE):
            continue

        # H3 level headings (#### or S1/S2 etc domain headers)
        if line.startswith('####') or re.match(r'^#+\s+S[1-6]\s+', line):
            text = re.sub(r'^#+\s*', '', line).strip()
            story.append(h3(text, S))

        # H2 level headings
        elif re.match(r'^###\s+\d+\.', line):
            text = re.sub(r'^#+\s*', '', line).strip()
            # Skip sections we already rendered
            if any(skip in text for skip in ['Executive Summary', 'Profilo', 'Risultati per sezione']):
                continue
            story.append(h2(text, S))

        # Bullet points
        elif line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
            text = line[2:].strip()
            # Clean markdown bold
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            story.append(bullet(text, S))

        # Table rows - render as simple text
        elif '|' in line and line.count('|') >= 2:
            # Skip separator rows
            if re.match(r'^[\s|:-]+$', line):
                continue
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                row_text = '  |  '.join(cells)
                row_text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', row_text)
                story.append(Paragraph(row_text, S['body_small']))

        # Bold text (standalone)
        elif line.startswith('**') and line.endswith('**'):
            text = line.strip('*').strip()
            story.append(Paragraph(f"<b>{text}</b>", S['h3']))

        # Regular paragraph
        else:
            text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', line)
            text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
            if len(text) > 5:
                story.append(body(text, S))

    story.append(PageBreak())

    # ── METODOLOGIA E DISCLAIMER ───────────────────────────────────────────────
    story.append(h1("8. Metodologia", S))
    story.append(sp(4))
    for title, text in [
        ("Natura dell'assessment",
         "Valutazione non invasiva basata su questionario strutturato di 31 domande, organizzate in 6 sezioni operative. "
         "Non e' un audit tecnico, non include test di vulnerabilita o verifica configurazioni."),
        ("Scala di valutazione",
         "0=Assente, 1=Informale (prassi non documentata), 2=Parziale (processi non completi), "
         "3=Governato (processi formalizzati, documentati, revisionati)."),
        ("Score globale e pesi",
         "S1=10%, S2=20%, S3=25%, S4=20%, S5=15%, S6=10%. "
         "Il peso maggiore e' su Accessi (S3) e Continuita (S4) per riflettere l'impatto operativo diretto."),
        ("Cap Rule",
         "Se S3 o S4 hanno score <=1.2, il livello complessivo non puo superare 'Livello 2 - Consapevole'. "
         "Vulnerabilita critiche su accessi o continuita non sono compensabili da altri controlli."),
        ("Indice di Coerenza Normativa (ICN)",
         "S2x25% + S3x30% + S4x25% + S6x20%. Misura l'allineamento a IEC 62443 e NIS2."),
    ]:
        story.append(KeepTogether([Paragraph(f"<b>{title}</b>", S['h3']), body(text, S), sp(4)]))

    story.append(sp(8))
    story.append(h1("9. Disclaimer", S))
    story.append(sp(4))
    story.append(Paragraph(
        "Questo report e' un output di assessment di maturita OT basato su questionario strutturato. "
        "Non sostituisce audit tecnici, penetration test o certificazioni normative. Le raccomandazioni "
        "devono essere adattate al contesto specifico con il supporto di figure tecniche OT/IT qualificate. "
        "<b>Prodotto da: Riccardo Talarico - otready.tech</b>",
        S['disclaimer']))

    doc.build(story, onFirstPage=on_cover, onLaterPages=on_page)
    buffer.seek(0)
    return buffer


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'OTReady PDF Generator'})


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        body_data = request.get_json(force=True)
        report_text = body_data.get('report_text', '')

        if not report_text:
            return jsonify({'error': 'report_text is required'}), 400

        # Parse report data
        data = parse_report_text(report_text)

        # Generate PDF
        pdf_buffer = build_pdf_from_data(data, report_text)

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='OTReady_Report.pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
